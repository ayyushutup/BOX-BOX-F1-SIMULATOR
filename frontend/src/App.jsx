import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import StrategyTree from './components/StrategyTree'
import SensitivityAnalysis from './components/SensitivityAnalysis'
import VolatilityIndex from './components/VolatilityIndex'
import ScenarioControls from './components/ScenarioControls'
import PositionTower from './components/PositionTower'
import RaceControlStatus from './components/RaceControlStatus';
import PredictionPanel from './components/PredictionPanel'
import IncidentPredictor from './components/IncidentPredictor'
import ScenarioPicker from './components/ScenarioPicker'
import DriverStrategyPanel from './components/DriverStrategyPanel'
import OutcomeDistribution from './components/OutcomeDistribution'
import FinishDistributionChart from './components/FinishDistributionChart'
import ConfidenceIndex from './components/ConfidenceIndex'
import './index.css'

function App() {
  // Views: 'scenarios' | 'simulation'
  const [view, setView] = useState('scenarios')
  const [selectedDriver, setSelectedDriver] = useState(null)

  const [isLoading, setIsLoading] = useState(false)
  const [baselineState, setBaselineState] = useState(null) // Holds { cars: [] }
  const [predictions, setPredictions] = useState(null)

  const [activeScenario, setActiveScenario] = useState(null)
  const [currentModifiers, setCurrentModifiers] = useState({})

  // Fetch prediction from the stateless backend
  const fetchPrediction = useCallback(async (scenario, modifiers = {}) => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/scenarios/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: scenario.id,
          modifiers: modifiers
        })
      })

      if (!response.ok) throw new Error('Failed to fetch prediction')

      const data = await response.json()

      setBaselineState(data.baseline_state)
      setPredictions(data.predictions)
      setCurrentModifiers(modifiers)
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleSelectScenario = async (scenarioId) => {
    // 1. Fetch scenario details to get the metadata
    try {
      const res = await fetch(`http://localhost:8000/api/scenarios/${scenarioId}`)
      const data = await res.json()
      if (data.scenario) {
        setActiveScenario(data.scenario)
        setView('simulation')
        // 2. Initial prediction fetch with no modifiers
        await fetchPrediction(data.scenario, {})
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleBackToScenarios = () => {
    setView('scenarios')
    setBaselineState(null)
    setPredictions(null)
    setActiveScenario(null)
    setCurrentModifiers({})
  }

  const handleModifiersChange = useCallback((newModifiers) => {
    if (activeScenario) {
      fetchPrediction(activeScenario, { ...currentModifiers, ...newModifiers })
    }
  }, [activeScenario, currentModifiers, fetchPrediction])


  // ==================
  // VIEW: SCENARIOS
  // ==================
  if (view === 'scenarios') {
    return <ScenarioPicker onSelectScenario={handleSelectScenario} />
  }

  // ==================
  // VIEW: SIMULATION (Stateless Engine Dashboard)
  // ==================
  return (
    <div className="app-container">
      {/* Scenario Header */}
      <div className="race-controls-header" style={{ position: 'absolute', top: 10, left: 10, zIndex: 100, display: 'flex', gap: '8px', alignItems: 'center' }}>
        <button className="btn-back" onClick={handleBackToScenarios}>
          ← SCENARIOS
        </button>
        {activeScenario && (
          <div className="scenario-active-badge">
            <span className="scenario-active-icon">{activeScenario.icon}</span>
            <span className="scenario-active-name">{activeScenario.name}</span>
          </div>
        )}
      </div>

      <Header
        lap={activeScenario?.starting_lap || 0}
        totalLaps={activeScenario?.total_laps || 0}
        time={0}
      />

      <div className="w-full relative" style={{ paddingBottom: '120px' }}>
        {/* Pass down modifying handler to the Scenario Controls */}
        <ScenarioControls onModifierChange={handleModifiersChange} isLoading={isLoading} />

        {/* NEW 3-ZONE LAYOUT */}
        <main style={{ display: 'grid', gridTemplateColumns: '1.2fr 2fr 1.2fr', gap: '16px', height: 'calc(100vh - 210px)', opacity: isLoading ? 0.5 : 1, transition: 'opacity 0.2s ease' }}>

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
            <OutcomeDistribution predictions={predictions} raceState={baselineState} />
            <FinishDistributionChart predictions={predictions} selectedDriver={selectedDriver} />
          </div>

          {/* RIGHT: Decision Tree + Sensitivity + Volatility */}
          <div className="zone-right" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            <StrategyTree raceState={baselineState} />
            <SensitivityAnalysis raceState={baselineState} />
            <VolatilityIndex raceState={baselineState} />
            <ConfidenceIndex predictions={predictions} />
            <PredictionPanel predictions={predictions} raceState={baselineState} />
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