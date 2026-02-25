import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import StrategyTree from './components/StrategyTree'
import SensitivityAnalysis from './components/SensitivityAnalysis'
import VolatilityIndex from './components/VolatilityIndex'
import ScenarioControls from './components/ScenarioControls'
import PositionTower from './components/PositionTower'
import RaceControlStatus from './components/RaceControlStatus'
import PredictionPanel from './components/PredictionPanel'
import IncidentPredictor from './components/IncidentPredictor'
import ScenarioLaboratory from './components/ScenarioLaboratory'
import DriverStrategyPanel from './components/DriverStrategyPanel'
import OutcomeDistribution from './components/OutcomeDistribution'
import FinishDistributionChart from './components/FinishDistributionChart'
import Home from './components/Home'
import './index.css'

function App() {
  // Views: 'home' | 'laboratory' | 'simulation'
  const [view, setView] = useState('home')
  const [selectedDriver, setSelectedDriver] = useState(null)

  const [isLoading, setIsLoading] = useState(false)
  const [baselineState, setBaselineState] = useState(null) // Holds { cars: [] }
  const [baselinePredictions, setBaselinePredictions] = useState(null) // Holds the untouched initial predictions
  const [predictions, setPredictions] = useState(null)

  // We store the full configuration for the current simulation
  const [activeConfig, setActiveConfig] = useState(null)
  const [activeScenarioName, setActiveScenarioName] = useState("")

  // Fetch prediction from the stateless backend
  const fetchPrediction = useCallback(async (configPayload) => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/scenarios/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configPayload)
      })

      if (!response.ok) throw new Error('Failed to fetch prediction')

      const data = await response.json()

      setBaselineState(data.baseline_state)
      setPredictions(data.predictions)
      if (!baselinePredictions) {
        setBaselinePredictions(data.predictions)
      }
      setActiveConfig(configPayload)
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleLaunchSimulation = async (type, config) => {
    // In the new system, 'type' is always 'custom' and 'config' is the full ScenarioConfig JSON
    setActiveScenarioName("Custom Laboratory Setup")
    setView('simulation')
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

  const handleModifiersChange = useCallback((newModifiers) => {
    if (activeConfig) {
      // Re-fetch prediction with updated chaos or other modifiers
      const updatedConfig = { ...activeConfig };

      // Map from ScenarioControls shallow dictionary to our deep ScenarioConfig mapping
      if (newModifiers.sc_prob) {
        updatedConfig.chaos = { ...updatedConfig.chaos, safety_car_probability: newModifiers.sc_prob };
      }
      if (newModifiers.chaos_base) {
        updatedConfig.chaos = { ...updatedConfig.chaos, incident_frequency: newModifiers.chaos_base };
      }
      if (newModifiers.tire_deg) {
        updatedConfig.engineering = { ...updatedConfig.engineering, tire_deg_multiplier: newModifiers.tire_deg };
      }
      if (newModifiers.weather) {
        const rainProb = newModifiers.weather === 'RAIN' ? 1.0 : 0.0;
        updatedConfig.weather = {
          ...updatedConfig.weather,
          timeline: [{ start_lap: 0, rain_probability: rainProb, temperature: rainProb ? 18.0 : 25.0 }]
        };
      }
      if (newModifiers.aggression) {
        // Apply to all drivers if a global slider is used
        const newDrivers = { ...updatedConfig.drivers };
        updatedConfig.race_structure.grid.forEach(car => {
          newDrivers[car.driver] = { ...(newDrivers[car.driver] || {}), aggression: newModifiers.aggression };
        });
        updatedConfig.drivers = newDrivers;
      }

      setActiveConfig(updatedConfig);
      fetchPrediction(updatedConfig);
    }
  }, [activeConfig, fetchPrediction])


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

      <div className="w-full relative" style={{ paddingBottom: '120px' }}>
        {/* Pass down modifying handler to the Scenario Controls */}
        <ScenarioControls onModifierChange={handleModifiersChange} isLoading={isLoading} />

        {/* NEW 3-ZONE LAYOUT */}
        <main style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr 1.2fr', gap: '16px', height: 'calc(100vh - 210px)' }}>

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
            <RaceControlStatus raceState={null} />
          </div>

          {/* CENTER: Probability (Hero) + EV Graphs */}
          <div className="zone-center" style={{ display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto', paddingRight: '4px' }}>
            <OutcomeDistribution predictions={predictions} baselinePredictions={baselinePredictions} raceState={baselineState} />
            <FinishDistributionChart predictions={predictions} baselinePredictions={baselinePredictions} selectedDriver={selectedDriver} />
          </div>

          {/* RIGHT: Decision Tree + Sensitivity + Volatility */}
          <div className="zone-right" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            <StrategyTree raceState={baselineState} />
            <SensitivityAnalysis raceState={baselineState} />
            <VolatilityIndex raceState={baselineState} activeConfig={activeConfig} />
            <PredictionPanel predictions={predictions} raceState={baselineState} activeConfig={activeConfig} />
            <IncidentPredictor raceState={baselineState} />
          </div>

        </main>

        {/* BOTTOM: Driver Strategy Breakdown (Replaces Telemetry) */}
        {selectedDriver && (() => {
          const selectedCar = baselineState?.cars?.find(c => c.driver === selectedDriver);
          if (!selectedCar) return null;
          return (
            <div className="w-full mt-4">
              <DriverStrategyPanel car={selectedCar} raceState={baselineState} />
            </div>
          );
        })()}

      </div>
    </div>
  )
}

export default App