import { useState, useEffect, useCallback, useRef, lazy, Suspense } from 'react'
import ScenarioLaboratory from './components/ScenarioLaboratory'
import Home from './components/Home'
import PredictionLoader from './components/PredictionLoader'
import { apiUrl } from './utils/api'
import './index.css'

const Header = lazy(() => import('./components/Header'))
const StrategyTree = lazy(() => import('./components/StrategyTree'))
const SensitivityAnalysis = lazy(() => import('./components/SensitivityAnalysis'))
const VolatilityIndex = lazy(() => import('./components/VolatilityIndex'))
const PositionTower = lazy(() => import('./components/PositionTower'))
const RaceControlStatus = lazy(() => import('./components/RaceControlStatus'))
const PredictionPanel = lazy(() => import('./components/PredictionPanel'))
const DriverStrategyPanel = lazy(() => import('./components/DriverStrategyPanel'))
const OutcomeDistribution = lazy(() => import('./components/OutcomeDistribution'))
const FinishDistributionChart = lazy(() => import('./components/FinishDistributionChart'))
const WinSharePieChart = lazy(() => import('./components/WinSharePieChart'))
const PodiumPieChart = lazy(() => import('./components/PodiumPieChart'))
const TireDegradationChart = lazy(() => import('./components/TireDegradationChart'))
const LapTimeComparisonChart = lazy(() => import('./components/LapTimeComparisonChart'))
const RaceCommentary = lazy(() => import('./components/RaceCommentary'))
const RaceTimelineChart = lazy(() => import('./components/RaceTimelineChart'))
const StrategyRecommendation = lazy(() => import('./components/StrategyRecommendation'))
const StateEstimationCard = lazy(() => import('./components/StateEstimationCard'))
const RaceAlerts = lazy(() => import('./components/RaceAlerts'))
const InteractiveEngineer = lazy(() => import('./components/InteractiveEngineer'))

const deepClone = (value) => {
  if (typeof structuredClone === 'function') {
    return structuredClone(value)
  }
  return JSON.parse(JSON.stringify(value))
}

function App() {
  // Views: 'home' | 'laboratory' | 'simulation'
  const [view, setView] = useState('home')
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [mobileActiveSection, setMobileActiveSection] = useState('analysis')
  const [mobileControlsOpen, setMobileControlsOpen] = useState(false)

  const [isMobile, setIsMobile] = useState(false)
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth <= 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);


  const [isLoading, setIsLoading] = useState(false)
  const [baselineState, setBaselineState] = useState(null)
  const [baselinePredictions, setBaselinePredictions] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [commentary, setCommentary] = useState(null)
  const [reasoningTree, setReasoningTree] = useState(null)

  const [activeConfig, setActiveConfig] = useState(null)
  const [activeScenarioName, setActiveScenarioName] = useState("")
  const [analysisDepth, setAnalysisDepth] = useState('overview')

  const [engineHealth, setEngineHealth] = useState({ status: 'checking', message: 'Checking engine...' })

  const activeConfigRef = useRef(activeConfig);
  const baselinePredictionsRef = useRef(baselinePredictions);
  const requestSequenceRef = useRef(0);
  const activeRequestRef = useRef(null);
  const modifiersDebounceRef = useRef(null);

  useEffect(() => { activeConfigRef.current = activeConfig; }, [activeConfig]);
  useEffect(() => { baselinePredictionsRef.current = baselinePredictions; }, [baselinePredictions]);
  useEffect(() => {
    if (!selectedDriver && baselineState?.cars?.length) {
      setSelectedDriver(baselineState.cars[0].driver);
    }
  }, [baselineState, selectedDriver]);

  useEffect(() => {
    return () => {
      if (modifiersDebounceRef.current) {
        clearTimeout(modifiersDebounceRef.current);
      }
      if (activeRequestRef.current) {
        activeRequestRef.current.abort();
      }
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const probeEngine = async () => {
      try {
        const response = await fetch(apiUrl('/health'), {
          method: 'GET',
          cache: 'no-store',
        });
        if (cancelled) return;
        if (response.ok) {
          setEngineHealth({ status: 'online', message: 'Prediction Engine Online' });
        } else {
          setEngineHealth({ status: 'offline', message: `Engine unreachable (${response.status})` });
        }
      } catch {
        if (!cancelled) {
          setEngineHealth({ status: 'offline', message: 'Engine offline' });
        }
      }
    };

    probeEngine();
    const timer = setInterval(probeEngine, 8000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  // Core fetch function — does NOT touch activeConfig to avoid feedback loops
  const fetchPrediction = useCallback(async (configPayload, options = {}) => {
    const { tier = 'full', showLoader = true } = options;
    const requestId = requestSequenceRef.current + 1;
    requestSequenceRef.current = requestId;

    if (activeRequestRef.current) {
      activeRequestRef.current.abort();
    }

    const controller = new AbortController();
    activeRequestRef.current = controller;

    if (showLoader) {
      setIsLoading(true);
    }

    try {
      const query = new URLSearchParams({
        mode: 'standard',
        intensity: 'cinematic_high',
        prediction_tier: tier,
      })
      const response = await fetch(`${apiUrl('/api/scenarios/predict')}?${query.toString()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configPayload),
        signal: controller.signal
      })

      if (!response.ok) {
        let serverMessage = 'Failed to fetch prediction'
        try {
          const errBody = await response.json()
          if (errBody?.detail?.message) {
            serverMessage = errBody.detail.message
          }
        } catch {
          // Keep default message
        }
        throw new Error(serverMessage)
      }

      const data = await response.json()
      if (requestId !== requestSequenceRef.current) {
        return { ok: false, error: 'Superseded by a newer request.' };
      }

      setBaselineState(data.baseline_state)
      setPredictions(data.predictions)
      setCommentary(data.commentary || null)
      setReasoningTree(data.reasoning_tree || null)
      setEngineHealth({ status: 'online', message: 'Prediction Engine Online' })
      if (!baselinePredictionsRef.current) {
        setBaselinePredictions(data.predictions)
      }
      // NOTE: We do NOT call setActiveConfig here — the caller is responsible for that
      return { ok: true, error: null };
    } catch (err) {
      if (err.name === 'AbortError') {
        return { ok: false, error: 'Request aborted.' };
      }
      console.error(err)
      const engineUrl = apiUrl('/api/scenarios/predict')
      setEngineHealth({ status: 'offline', message: `Engine unavailable at ${engineUrl}` })
      return {
        ok: false,
        error: `Could not reach Prediction Engine at ${engineUrl}. ${err.message || 'Network error.'}`
      };
    } finally {
      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null;
      }
      if (showLoader) {
        setIsLoading(false)
      }
    }
  }, [])

  const handleLaunchSimulation = async (type, config) => {
    setActiveScenarioName("Custom Laboratory Setup")
    setView('simulation')
    setMobileActiveSection('analysis')
    setActiveConfig(config)
    const result = await fetchPrediction(config, { tier: 'full', showLoader: true })
    if (!result.ok) {
      alert(result.error || "Failed to connect to the Prediction Engine. Please ensure the backend is running.")
      setView('laboratory')
    }
  }

  const handleBackToLaboratory = () => {
    if (modifiersDebounceRef.current) {
      clearTimeout(modifiersDebounceRef.current);
      modifiersDebounceRef.current = null;
    }
    if (activeRequestRef.current) {
      activeRequestRef.current.abort();
      activeRequestRef.current = null;
    }
    requestSequenceRef.current += 1;
    setView('laboratory')
    setBaselineState(null)
    setPredictions(null)
    setBaselinePredictions(null)
    setActiveConfig(null)
    setActiveScenarioName("")
    setMobileControlsOpen(false)
  }

  // Scenario Injector handler — reads config from ref, never from closure
  const handleModifiersChange = useCallback((newModifiers) => {
    const currentConfig = activeConfigRef.current;
    if (!currentConfig) return;

    const updatedConfig = deepClone(currentConfig);

    if (newModifiers.sc_prob !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), safety_car_probability: newModifiers.sc_prob };
    }
    if (newModifiers.chaos_base !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), incident_frequency: newModifiers.chaos_base };
    }
    if (newModifiers.tire_deg !== undefined) {
      updatedConfig.engineering = { ...(updatedConfig.engineering || {}), tire_deg_multiplier: newModifiers.tire_deg };
    }
    if (newModifiers.weather) {
      const rainProb = newModifiers.weather === 'RAIN' ? 1.0 : 0.0;
      updatedConfig.weather = {
        ...(updatedConfig.weather || {}),
        timeline: [{ start_lap: 0, rain_probability: rainProb, temperature: rainProb ? 18.0 : 25.0 }]
      };
    }
    if (newModifiers.aggression !== undefined && updatedConfig.race_structure?.grid) {
      const newDrivers = { ...(updatedConfig.drivers || {}) };
      updatedConfig.race_structure.grid.forEach(car => {
        newDrivers[car.driver] = { ...(newDrivers[car.driver] || {}), aggression: newModifiers.aggression };
      });
      updatedConfig.drivers = newDrivers;
    }
    if (newModifiers.field_compression !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), field_compression: newModifiers.field_compression };
    }
    if (newModifiers.reliability !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), reliability_variance: newModifiers.reliability };
    }
    if (newModifiers.qualifying_delta !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), qualifying_delta_override: newModifiers.qualifying_delta };
    }
    if (newModifiers.form_drift !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), driver_form_drift: newModifiers.form_drift };
    }
    if (newModifiers.chaos_scaling !== undefined) {
      updatedConfig.chaos = { ...(updatedConfig.chaos || {}), chaos_scaling: newModifiers.chaos_scaling };
    }

    setActiveConfig(updatedConfig);
    fetchPrediction(updatedConfig, { tier: 'preview', showLoader: false });

    if (modifiersDebounceRef.current) {
      clearTimeout(modifiersDebounceRef.current);
    }
    modifiersDebounceRef.current = setTimeout(() => {
      fetchPrediction(updatedConfig, { tier: 'full', showLoader: true });
    }, 300);
  }, [fetchPrediction]) // fetchPrediction is stable (empty deps), so this callback is also stable

  // Engineer commands handler — also reads from ref
  const handleEngineerCommand = useCallback((driverId, command) => {
    const currentConfig = activeConfigRef.current;
    if (!currentConfig || !driverId) return;
    const updatedConfig = deepClone(currentConfig);

    updatedConfig.drivers = updatedConfig.drivers || {};
    const driverCfg = updatedConfig.drivers[driverId] || { aggression: 1.0, tire_preservation: 1.0, risk_tolerance: 1.0 };

    const carIndex = updatedConfig.race_structure.grid.findIndex(c => c.driver === driverId);
    if (carIndex === -1) return;

    const car = updatedConfig.race_structure.grid[carIndex];

    switch (command) {
      case 'BOX':
        car.pit_stops = (car.pit_stops || 0) + 1;
        car.tire_age = 0;
        car.tire_wear = 0;
        car.tire_compound = (car.tire_compound === 'MEDIUM') ? 'HARD' : 'MEDIUM';
        break;
      case 'PUSH':
        driverCfg.aggression = Math.min(2.0, (driverCfg.aggression || 1.0) + 0.3);
        driverCfg.tire_preservation = Math.max(0.0, (driverCfg.tire_preservation || 1.0) - 0.3);
        driverCfg.risk_tolerance = Math.min(2.0, (driverCfg.risk_tolerance || 1.0) + 0.3);
        break;
      case 'SAVE_TIRES':
        driverCfg.aggression = Math.max(0.0, (driverCfg.aggression || 1.0) - 0.3);
        driverCfg.tire_preservation = Math.min(2.0, (driverCfg.tire_preservation || 1.0) + 0.3);
        driverCfg.risk_tolerance = Math.max(0.0, (driverCfg.risk_tolerance || 1.0) - 0.3);
        break;
      default:
        break;
    }

    updatedConfig.drivers[driverId] = driverCfg;
    setActiveConfig(updatedConfig);
    fetchPrediction(updatedConfig, { tier: 'full', showLoader: true });
  }, [fetchPrediction])

  // ==================
  // View: HOME
  // ==================
  if (view === 'home') {
    return <Home onNavigate={(v) => setView(v === 'scenarios' ? 'laboratory' : v)} />
  }

  // ==================
  // View: LABORATORY
  // ==================
  if (view === 'laboratory') {
    return <ScenarioLaboratory onSelectScenario={handleLaunchSimulation} onBackToHome={() => setView('home')} />
  }

  const hasPredictedStandings = Boolean(
    predictions?.predicted_order?.length || predictions?.mc_win_distribution
  )

  const displayedStandingsCars = (() => {
    const baseCars = baselineState?.cars || []
    if (!hasPredictedStandings || baseCars.length === 0) return baseCars

    const byDriver = new Map(baseCars.map((c) => [c.driver, c]))
    const orderedDrivers = predictions?.predicted_order?.length
      ? predictions.predicted_order
      : Object.entries(predictions?.mc_win_distribution || {})
        .sort((a, b) => b[1] - a[1])
        .map(([driver]) => driver)

    const ranked = []
    const seen = new Set()

    orderedDrivers.forEach((driver, idx) => {
      const car = byDriver.get(driver)
      if (car) {
        ranked.push({ ...car, position: idx + 1 })
        seen.add(driver)
      }
    })

    baseCars
      .filter((c) => !seen.has(c.driver))
      .sort((a, b) => (a.position || 999) - (b.position || 999))
      .forEach((c) => ranked.push({ ...c, position: ranked.length + 1 }))

    return ranked
  })()

  const mobileDriverChips = displayedStandingsCars.slice(0, 8)

  const renderLiveControls = (showEngineer = false) => {
    if (!activeConfig) return null
    return (
      <div className="panel" style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <h3 style={{ margin: 0, fontSize: '0.75rem', letterSpacing: '1px', color: '#bbb' }}>LIVE SCENARIO CONTROLS</h3>
        <label style={{ fontSize: '0.65rem', color: '#888' }}>
          Safety Car: {(activeConfig?.chaos?.safety_car_probability ?? 1).toFixed(2)}x
          <input
            type="range"
            min="0"
            max="3"
            step="0.1"
            value={activeConfig?.chaos?.safety_car_probability ?? 1}
            onChange={(e) => handleModifiersChange({ sc_prob: parseFloat(e.target.value) })}
            style={{ width: '100%', marginTop: '4px' }}
          />
        </label>
        <label style={{ fontSize: '0.65rem', color: '#888' }}>
          Incident Freq: {(activeConfig?.chaos?.incident_frequency ?? 1).toFixed(2)}x
          <input
            type="range"
            min="0"
            max="3"
            step="0.1"
            value={activeConfig?.chaos?.incident_frequency ?? 1}
            onChange={(e) => handleModifiersChange({ chaos_base: parseFloat(e.target.value) })}
            style={{ width: '100%', marginTop: '4px' }}
          />
        </label>
        <label style={{ fontSize: '0.65rem', color: '#888' }}>
          Tire Deg: {(activeConfig?.engineering?.tire_deg_multiplier ?? 1).toFixed(2)}x
          <input
            type="range"
            min="0"
            max="3"
            step="0.1"
            value={activeConfig?.engineering?.tire_deg_multiplier ?? 1}
            onChange={(e) => handleModifiersChange({ tire_deg: parseFloat(e.target.value) })}
            style={{ width: '100%', marginTop: '4px' }}
          />
        </label>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            className="btn"
            onClick={() => handleModifiersChange({ weather: 'DRY' })}
            disabled={isLoading}
            style={{ flex: 1, minHeight: '44px' }}
          >
            DRY
          </button>
          <button
            className="btn"
            onClick={() => handleModifiersChange({ weather: 'RAIN' })}
            disabled={isLoading}
            style={{ flex: 1, minHeight: '44px' }}
          >
            RAIN
          </button>
        </div>
        {showEngineer && (
          <InteractiveEngineer selectedDriver={selectedDriver} onCommand={handleEngineerCommand} disabled={isLoading} />
        )}
      </div>
    )
  }

  // ==================
  // View: SIMULATION (Stateless Engine Dashboard)
  // ==================
  return (
    <Suspense fallback={<div className="app-container"><PredictionLoader isLoading={true} /></div>}>
      <div className="app-container">
        <PredictionLoader isLoading={isLoading} />
      {/* Scenario Header */}
      {!isMobile && (
        <div className="race-controls-header" style={{ position: 'absolute', top: 10, left: 10, zIndex: 100, display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button className="btn-back" onClick={handleBackToLaboratory}>
            ← LABORATORY
          </button>
          {activeScenarioName && (
            <div className="scenario-active-badge">
              <span className="scenario-active-icon">🧪</span>
              <span className="scenario-active-name">{activeScenarioName}</span>
            </div>
          )}
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 10px',
              borderRadius: '999px',
              border: '1px solid rgba(255,255,255,0.16)',
              background: 'rgba(0,0,0,0.55)',
              color: engineHealth.status === 'online' ? '#9cf2b8' : engineHealth.status === 'offline' ? '#ffb3b3' : '#e2e2e2',
              fontSize: '0.68rem',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
            title={engineHealth.message}
          >
            <span
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '999px',
                background: engineHealth.status === 'online' ? '#18d267' : engineHealth.status === 'offline' ? '#ff4d4f' : '#b4b4b4',
              }}
            />
            {engineHealth.status}
          </div>
        </div>
      )}

      {isMobile && (
        <div className="mobile-sim-header">
          <div className="mobile-sim-toprow">
            <button className="btn-back" onClick={handleBackToLaboratory}>← LAB</button>
            <div className="mobile-sim-title">{activeScenarioName || 'Simulation'}</div>
            <button className="btn" onClick={() => setMobileControlsOpen(v => !v)} style={{ minHeight: '40px', minWidth: '76px' }}>
              CONTROLS
            </button>
          </div>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              alignSelf: 'flex-start',
              marginTop: '6px',
              padding: '4px 8px',
              borderRadius: '999px',
              border: '1px solid rgba(255,255,255,0.16)',
              background: 'rgba(0,0,0,0.45)',
              color: engineHealth.status === 'online' ? '#9cf2b8' : engineHealth.status === 'offline' ? '#ffb3b3' : '#e2e2e2',
              fontSize: '0.62rem',
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
            }}
            title={engineHealth.message}
          >
            <span
              style={{
                width: '7px',
                height: '7px',
                borderRadius: '999px',
                background: engineHealth.status === 'online' ? '#18d267' : engineHealth.status === 'offline' ? '#ff4d4f' : '#b4b4b4',
              }}
            />
            {engineHealth.status}
          </div>
          {mobileDriverChips.length > 0 && (
            <div className="mobile-driver-row no-scrollbar">
              {mobileDriverChips.map((c) => (
                <button
                  key={c.driver}
                  className={`mobile-driver-chip ${selectedDriver === c.driver ? 'active' : ''}`}
                  onClick={() => setSelectedDriver(c.driver)}
                >
                  {c.driver}
                </button>
              ))}
            </div>
          )}
          <div className="mobile-section-tabs">
            <button
              className={`mobile-section-tab ${mobileActiveSection === 'standings' ? 'active' : ''}`}
              onClick={() => setMobileActiveSection('standings')}
            >
              STANDINGS
            </button>
            <button
              className={`mobile-section-tab ${mobileActiveSection === 'analysis' ? 'active' : ''}`}
              onClick={() => setMobileActiveSection('analysis')}
            >
              ANALYSIS
            </button>
            <button
              className={`mobile-section-tab ${mobileActiveSection === 'predictions' ? 'active' : ''}`}
              onClick={() => setMobileActiveSection('predictions')}
            >
              PREDICT
            </button>
          </div>
        </div>
      )}

      {!isMobile && (
        <Header
          lap={activeConfig?.race_structure?.starting_lap || 0}
          totalLaps={activeConfig?.race_structure?.total_laps || 0}
          time={0}
        />
      )}

      <div className="w-full relative">

        {/* New 3-ZONE LAYOUT */}
        <main className="simulation-main-grid" style={{ gap: '16px', minHeight: isMobile ? 'auto' : 'calc(100vh - 210px)', paddingBottom: isMobile ? '130px' : '0', marginTop: isMobile ? '8px' : '16px' }}>

          {/* Left: Standings + Scenario Controls */}
          <div className={`zone-left ${isMobile && mobileActiveSection !== 'standings' ? 'mobile-hidden' : ''}`} style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
            <div className="panel tower-panel" style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <h2 className="panel-title" style={{ flexShrink: 0 }}>{hasPredictedStandings ? 'FINAL STANDINGS' : 'BASELINE STANDINGS'}</h2>
              <PositionTower
                cars={displayedStandingsCars}
                onSelectDriver={setSelectedDriver}
                selectedDriver={selectedDriver}
              />
            </div>

            {!isMobile && <RaceControlStatus raceState={baselineState} />}
            {!isMobile && renderLiveControls(false)}
          </div>

          {/* Center: Charts with View Toggle */}
          <div className={`zone-center ${isMobile && mobileActiveSection !== 'analysis' ? 'mobile-hidden' : ''}`} style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '4px' }}>

            {/* Analysis Depth Toggle */}
            <div style={{ display: 'flex', justifyContent: isMobile ? 'stretch' : 'center', gap: '0' }}>
              <div style={{ display: 'flex', background: 'rgba(0,0,0,0.5)', borderRadius: '6px', border: '1px solid #333', overflow: 'hidden' }}>
                <button
                  onClick={() => setAnalysisDepth('overview')}
                  style={{ padding: isMobile ? '10px 14px' : '6px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '1px', border: 'none', background: analysisDepth === 'overview' ? 'var(--cyan)' : 'transparent', color: analysisDepth === 'overview' ? '#000' : '#888', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  🎯 OVERVIEW
                </button>
                <button
                  onClick={() => setAnalysisDepth('deep')}
                  style={{ padding: isMobile ? '10px 14px' : '6px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '1px', border: 'none', borderLeft: '1px solid #333', background: analysisDepth === 'deep' ? '#a855f7' : 'transparent', color: analysisDepth === 'deep' ? '#000' : '#888', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  📊 DEEP ANALYSIS
                </button>
              </div>
            </div>


            {analysisDepth === 'overview' ? (
              <>
                {/* Decision Layer: What matters most */}
                <OutcomeDistribution predictions={predictions} baselinePredictions={baselinePredictions} raceState={baselineState} />
                <RaceTimelineChart predictions={predictions} selectedDriver={selectedDriver} />
                <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />
                {!isMobile && <TireDegradationChart raceState={baselineState} activeConfig={activeConfig} />}
              </>
            ) : (
              <>
                {/* Deep Analytics Layer */}
                <div className="analytics-grid" style={{ gap: '16px' }}>
                  <WinSharePieChart predictions={predictions} />
                  {!isMobile && <PodiumPieChart predictions={predictions} />}
                </div>
                {!isMobile && <LapTimeComparisonChart raceState={baselineState} predictions={predictions} />}
                <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />
              </>
            )}
          </div>

          {/* Right: Decision Tree + Sensitivity + Volatility */}
          <div className={`zone-right ${isMobile && mobileActiveSection !== 'predictions' ? 'mobile-hidden' : ''}`} style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            <PredictionPanel predictions={predictions} raceState={baselineState} activeConfig={activeConfig} />
            <RaceAlerts predictions={predictions} />
            {!isMobile && <InteractiveEngineer selectedDriver={selectedDriver} onCommand={handleEngineerCommand} disabled={isLoading} />}
            <StrategyRecommendation predictions={predictions} selectedDriver={selectedDriver} />
            {isMobile && <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />}
            {!isMobile && <StateEstimationCard predictions={predictions} selectedDriver={selectedDriver} />}
            {!isMobile && <StrategyTree raceState={baselineState} />}
            {!isMobile && <SensitivityAnalysis raceState={baselineState} predictions={predictions} baselinePredictions={baselinePredictions} />}
            {!isMobile && <VolatilityIndex raceState={baselineState} activeConfig={activeConfig} />}
          </div>

        </main>

        {/* Bottom: Driver Strategy Breakdown */}
        {!isMobile && selectedDriver && (() => {
          const selectedCar = baselineState?.cars?.find(c => c.driver === selectedDriver);
          if (!selectedCar) return null;
          return (
            <div className={`w-full mt-4 ${isMobile ? 'mb-20' : ''}`}>
              <DriverStrategyPanel car={selectedCar} raceState={baselineState} predictions={predictions} />
            </div>
          );
        })()}

        {/* AI RACE COMMENTARY — Full-Width Bottom Panel */}
        <div style={{ marginTop: '16px', padding: '0 12px', marginBottom: '0' }}>
          <RaceCommentary
            commentary={commentary}
            reasoningTree={reasoningTree}
          />
        </div>

        {/* Mobile CONTROLS DRAWER */}
        {isMobile && mobileControlsOpen && (
          <>
            <div className="mobile-controls-scrim" onClick={() => setMobileControlsOpen(false)} />
            <div className="mobile-controls-sheet no-scrollbar">
              {renderLiveControls(true)}
            </div>
          </>
        )}

      </div>
    </div>
    </Suspense>
  )
}

export default App
