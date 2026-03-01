import { useState, useEffect, useCallback, useRef } from 'react'
import Header from './components/Header'
import StrategyTree from './components/StrategyTree'
import SensitivityAnalysis from './components/SensitivityAnalysis'
import VolatilityIndex from './components/VolatilityIndex'
import ScenarioControls from './components/ScenarioControls'
import PositionTower from './components/PositionTower'
import RaceControlStatus from './components/RaceControlStatus'
import PredictionPanel from './components/PredictionPanel'

import ScenarioLaboratory from './components/ScenarioLaboratory'
import DriverStrategyPanel from './components/DriverStrategyPanel'
import OutcomeDistribution from './components/OutcomeDistribution'
import FinishDistributionChart from './components/FinishDistributionChart'
import Home from './components/Home'
import InteractiveEngineer from './components/InteractiveEngineer'
import WinSharePieChart from './components/WinSharePieChart'
import PodiumPieChart from './components/PodiumPieChart'
import TireDegradationChart from './components/TireDegradationChart'
import LapTimeComparisonChart from './components/LapTimeComparisonChart'
import RaceCommentary from './components/RaceCommentary'
import './index.css'

function App() {
  // Views: 'home' | 'laboratory' | 'simulation'
  const [view, setView] = useState('home')
  const [selectedDriver, setSelectedDriver] = useState(null)

  const [isLoading, setIsLoading] = useState(false)
  const [baselineState, setBaselineState] = useState(null)
  const [baselinePredictions, setBaselinePredictions] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [commentary, setCommentary] = useState(null)
  const [reasoningTree, setReasoningTree] = useState(null)

  const [activeConfig, setActiveConfig] = useState(null)
  const [activeScenarioName, setActiveScenarioName] = useState("")
  const [analysisDepth, setAnalysisDepth] = useState('overview')

  const [commentaryMode, setCommentaryMode] = useState('standard')
  const [commentaryIntensity, setCommentaryIntensity] = useState('cinematic_high')

  const activeConfigRef = useRef(activeConfig);
  const baselinePredictionsRef = useRef(baselinePredictions);
  const isLoadingRef = useRef(isLoading);
  const commentaryModeRef = useRef(commentaryMode);
  const commentaryIntensityRef = useRef(commentaryIntensity);

  useEffect(() => { activeConfigRef.current = activeConfig; }, [activeConfig]);
  useEffect(() => { baselinePredictionsRef.current = baselinePredictions; }, [baselinePredictions]);
  useEffect(() => { isLoadingRef.current = isLoading; }, [isLoading]);
  useEffect(() => { commentaryModeRef.current = commentaryMode; }, [commentaryMode]);
  useEffect(() => { commentaryIntensityRef.current = commentaryIntensity; }, [commentaryIntensity]);

  // Core fetch function — does NOT touch activeConfig to avoid feedback loops
  const fetchPrediction = useCallback(async (configPayload) => {
    if (isLoadingRef.current) return; // Prevent overlapping requests
    setIsLoading(true)
    try {
      const mode = commentaryModeRef.current;
      const intensity = commentaryIntensityRef.current;
      const response = await fetch(`http://localhost:8000/api/scenarios/predict?mode=${mode}&intensity=${intensity}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configPayload)
      })

      if (!response.ok) throw new Error('Failed to fetch prediction')

      const data = await response.json()

      setBaselineState(data.baseline_state)
      setPredictions(data.predictions)
      setCommentary(data.commentary || null)
      setReasoningTree(data.reasoning_tree || null)
      if (!baselinePredictionsRef.current) {
        setBaselinePredictions(data.predictions)
      }
      // NOTE: We do NOT call setActiveConfig here — the caller is responsible for that
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleLaunchSimulation = async (type, config) => {
    setActiveScenarioName("Custom Laboratory Setup")
    setView('simulation')
    setActiveConfig(config)
    await fetchPrediction(config)
  }

  const handleBackToLaboratory = () => {
    setView('laboratory')
    setBaselineState(null)
    setPredictions(null)
    setBaselinePredictions(null)
    setActiveConfig(null)
    setActiveScenarioName("")
  }

  // Scenario Injector handler — reads config from ref, never from closure
  const handleModifiersChange = useCallback((newModifiers) => {
    const currentConfig = activeConfigRef.current;
    if (!currentConfig) return;

    // DEEP clone to prevent mutating React state
    const updatedConfig = JSON.parse(JSON.stringify(currentConfig));

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
    fetchPrediction(updatedConfig);
  }, [fetchPrediction]) // fetchPrediction is stable (empty deps), so this callback is also stable

  // Engineer commands handler — also reads from ref
  const handleEngineerCommand = useCallback((driverId, command) => {
    const currentConfig = activeConfigRef.current;
    if (!currentConfig || !driverId) return;
    const updatedConfig = JSON.parse(JSON.stringify(currentConfig));

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
    fetchPrediction(updatedConfig);
  }, [fetchPrediction])

  // Commentary controls handler
  const handleCommentaryModeChange = useCallback((newMode) => {
    setCommentaryMode(newMode);
    commentaryModeRef.current = newMode; // update ref immediately before fetch
    if (activeConfigRef.current) fetchPrediction(activeConfigRef.current);
  }, [fetchPrediction]);

  const handleCommentaryIntensityChange = useCallback((newIntensity) => {
    setCommentaryIntensity(newIntensity);
    commentaryIntensityRef.current = newIntensity; // update ref immediately before fetch
    if (activeConfigRef.current) fetchPrediction(activeConfigRef.current);
  }, [fetchPrediction]);



  // ==================
  // VIEW: HOME
  // ==================
  if (view === 'home') {
    return <Home onNavigate={(v) => setView(v === 'scenarios' ? 'laboratory' : v)} />
  }

  // ==================
  // VIEW: LABORATORY
  // ==================
  if (view === 'laboratory') {
    return <ScenarioLaboratory onSelectScenario={handleLaunchSimulation} onBackToHome={() => setView('home')} />
  }

  // ==================
  // VIEW: SIMULATION (Stateless Engine Dashboard)
  // ==================
  return (
    <div className="app-container">
      {/* Scenario Header */}
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
      </div>

      <Header
        lap={activeConfig?.race_structure?.starting_lap || 0}
        totalLaps={activeConfig?.race_structure?.total_laps || 0}
        time={0}
      />

      <div className="w-full relative">
        {/* Pass down modifying handler to the Scenario Controls */}
        <ScenarioControls onModifierChange={handleModifiersChange} isLoading={isLoading} />

        {/* NEW 3-ZONE LAYOUT */}
        <main style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr 1.2fr', gap: '16px', minHeight: 'calc(100vh - 210px)' }}>

          {/* LEFT: Standings + Scenario Controls */}
          <div className="zone-left" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'hidden' }}>
            <div className="panel tower-panel" style={{ flex: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <h2 className="panel-title" style={{ flexShrink: 0 }}>BASELINE STANDINGS</h2>
              <PositionTower
                cars={baselineState?.cars || []}
                onSelectDriver={setSelectedDriver}
                selectedDriver={selectedDriver}
              />
            </div>

            <InteractiveEngineer
              selectedDriver={selectedDriver}
              onCommand={handleEngineerCommand}
              disabled={isLoading}
            />

            <RaceControlStatus raceState={null} />
          </div>

          {/* CENTER: Charts with View Toggle */}
          <div className="zone-center" style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '4px' }}>

            {/* Analysis Depth Toggle */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0' }}>
              <div style={{ display: 'flex', background: 'rgba(0,0,0,0.5)', borderRadius: '6px', border: '1px solid #333', overflow: 'hidden' }}>
                <button
                  onClick={() => setAnalysisDepth('overview')}
                  style={{ padding: '6px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '1px', border: 'none', background: analysisDepth === 'overview' ? 'var(--cyan)' : 'transparent', color: analysisDepth === 'overview' ? '#000' : '#888', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  🎯 OVERVIEW
                </button>
                <button
                  onClick={() => setAnalysisDepth('deep')}
                  style={{ padding: '6px 16px', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '1px', border: 'none', borderLeft: '1px solid #333', background: analysisDepth === 'deep' ? '#a855f7' : 'transparent', color: analysisDepth === 'deep' ? '#000' : '#888', cursor: 'pointer', transition: 'all 0.2s' }}
                >
                  📊 DEEP ANALYSIS
                </button>
              </div>
            </div>


            {analysisDepth === 'overview' ? (
              <>
                {/* Decision Layer: What matters most */}
                <OutcomeDistribution predictions={predictions} baselinePredictions={baselinePredictions} raceState={baselineState} />
                <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />
                <TireDegradationChart raceState={baselineState} activeConfig={activeConfig} />
              </>
            ) : (
              <>
                {/* Deep Analytics Layer */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <WinSharePieChart predictions={predictions} />
                  <PodiumPieChart predictions={predictions} />
                </div>
                <LapTimeComparisonChart raceState={baselineState} predictions={predictions} />
                <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />
              </>
            )}
          </div>

          {/* RIGHT: Decision Tree + Sensitivity + Volatility */}
          <div className="zone-right" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            <PredictionPanel predictions={predictions} raceState={baselineState} activeConfig={activeConfig} />
            <StrategyTree raceState={baselineState} />
            <SensitivityAnalysis raceState={baselineState} predictions={predictions} baselinePredictions={baselinePredictions} />
            <VolatilityIndex raceState={baselineState} activeConfig={activeConfig} />
          </div>

        </main>

        {/* BOTTOM: Driver Strategy Breakdown */}
        {selectedDriver && (() => {
          const selectedCar = baselineState?.cars?.find(c => c.driver === selectedDriver);
          if (!selectedCar) return null;
          return (
            <div className="w-full mt-4">
              <DriverStrategyPanel car={selectedCar} raceState={baselineState} predictions={predictions} />
            </div>
          );
        })()}

        {/* AI RACE COMMENTARY — Full-Width Bottom Panel */}
        <div style={{ marginTop: '16px', padding: '0 12px' }}>
          <RaceCommentary
            commentary={commentary}
            reasoningTree={reasoningTree}
            mode={commentaryMode}
            intensity={commentaryIntensity}
            onModeChange={handleCommentaryModeChange}
            onIntensityChange={handleCommentaryIntensityChange}
            disabled={isLoading}
          />
        </div>

      </div>
    </div>
  )
}

export default App