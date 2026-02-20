import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import TrackMap from './components/TrackMap'
import PositionTower from './components/PositionTower'
import EventLog from './components/EventLog'
import Controls from './components/Controls'
import RaceControlStatus from './components/RaceControlStatus';
import TelemetryPanel from './components/TelemetryPanel'
import PredictionPanel from './components/PredictionPanel'
import AIEngineer from './components/AIEngineer'
import IncidentPredictor from './components/IncidentPredictor'
import RaceTimeline from './components/RaceTimeline'
import ScenarioPicker from './components/ScenarioPicker'
import ScenarioResults from './components/ScenarioResults'
import { useSoundEffects } from './hooks/useSoundEffects'
import './index.css'

function App() {
  // Views: 'scenarios' | 'simulation' | 'results'
  const [view, setView] = useState('scenarios')
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [trackMode, setTrackMode] = useState('SPECTATOR')

  const [isConnected, setIsConnected] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [raceState, setRaceState] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [speed, setSpeed] = useState(1)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [logCollapsed, setLogCollapsed] = useState(true)
  const [activeScenario, setActiveScenario] = useState(null)
  const [scenarioResult, setScenarioResult] = useState(null)
  const wsRef = useRef(null)
  const { processEvents } = useSoundEffects(soundEnabled)

  // Connect and init a scenario via WebSocket
  const connectToScenario = useCallback((scenarioId) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket('ws://localhost:8000/ws/race')
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Connected to Scenario Server')
      setIsConnected(true)
      ws.send(JSON.stringify({
        command: 'init_scenario',
        scenario_id: scenarioId
      }))
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'init') {
        setRaceState(message.data)
        if (message.scenario) {
          setActiveScenario(message.scenario)
        }
        if (message.data?.events) {
          processEvents(message.data.events)
        }
      } else if (message.type === 'update' || message.type === 'state') {
        setRaceState(message.data)
        if (message.data?.events) {
          processEvents(message.data.events)
        }
        if (message.predictions) {
          setPredictions(message.predictions)
        }
      } else if (message.type === 'finished') {
        setRaceState(message.data)
        setIsPlaying(false)
        // Auto-fetch results when scenario finishes
        if (activeScenario) {
          fetchResults(activeScenario.id)
        }
      }
    }

    ws.onclose = () => {
      console.log('Disconnected')
      setIsConnected(false)
      setIsPlaying(false)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close()
    }
  }, [activeScenario])

  const fetchResults = (scenarioId) => {
    fetch(`http://localhost:8000/api/scenarios/${scenarioId}/run`, { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        if (data.result) {
          setScenarioResult(data.result)
          setView('results')
        }
      })
      .catch(err => console.error('Failed to fetch results:', err))
  }

  const handleSelectScenario = (scenarioId) => {
    setView('simulation')
    setScenarioResult(null)
    connectToScenario(scenarioId)
  }

  const handleBackToScenarios = () => {
    if (wsRef.current) wsRef.current.close()
    setIsPlaying(false)
    setView('scenarios')
    setRaceState(null)
    setPredictions(null)
    setActiveScenario(null)
    setScenarioResult(null)
  }

  const handleViewResults = () => {
    if (activeScenario) {
      fetchResults(activeScenario.id)
    }
  }

  const handleReplay = () => {
    if (activeScenario) {
      handleSelectScenario(activeScenario.id)
    }
  }

  const handlePlay = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'start', speed }))
      setIsPlaying(true)
    }
  }, [speed])

  const handlePause = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'pause' }))
      setIsPlaying(false)
    }
  }, [])

  const handleStep = useCallback((count = 1) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'step', count }))
    }
  }, [])

  const handleSpeedChange = useCallback((newSpeed) => {
    setSpeed(newSpeed)
    if (isPlaying && wsRef.current) {
      wsRef.current.send(JSON.stringify({ command: 'start', speed: newSpeed }))
    }
  }, [isPlaying])

  const handleRaceControl = useCallback((type) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'event', type }))
    }
  }, [])

  const handleWeatherControl = useCallback((type) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'event', type: 'weather', value: type }))
    }
  }, [])

  const sendDriverCommand = useCallback((driver, cmd) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'driver_command', driver, cmd }))
    }
  }, [])

  // ==================
  // VIEW: SCENARIOS
  // ==================
  if (view === 'scenarios') {
    return <ScenarioPicker onSelectScenario={handleSelectScenario} />
  }

  // ==================
  // VIEW: RESULTS
  // ==================
  if (view === 'results') {
    return (
      <ScenarioResults
        result={scenarioResult}
        onBack={handleBackToScenarios}
        onReplay={handleReplay}
      />
    )
  }

  // ==================
  // VIEW: CONNECTING
  // ==================
  if (!isConnected && view === 'simulation') {
    return (
      <div className="app-container connecting-screen">
        <div className="race-loader">
          <h1>INITIALIZING SCENARIO</h1>
          <div className="pulse-bar"></div>
          <p>CONNECTING TO SIMULATION ENGINE ON PORT 8000</p>
        </div>
      </div>
    )
  }

  // ==================
  // VIEW: SIMULATION (Live playback)
  // ==================
  const isFinished = raceState?.is_finished

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
        <button
          className="btn-back"
          onClick={() => setSoundEnabled(!soundEnabled)}
          title={soundEnabled ? 'Mute' : 'Unmute'}
          style={{ minWidth: '36px', textAlign: 'center' }}
        >
          {soundEnabled ? '🔊' : '🔇'}
        </button>
        {isFinished && (
          <button className="btn-results" onClick={handleViewResults}>
            📊 VIEW RESULTS
          </button>
        )}
      </div>

      <Header
        lap={raceState?.lap || 0}
        totalLaps={raceState?.total_laps || 0}
        time={raceState?.time_ms || 0}
      />

      <div className="w-full relative" style={{ paddingBottom: '120px' }}>
        <main className="main-grid w-full">
          <div className="panel track-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h2 className="panel-title" style={{ marginBottom: 0 }}>TRACK MAP</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontWeight: 900, color: 'var(--text-dim)' }}>{raceState?.track?.name?.toUpperCase()}</span>
                <button
                  className="btn btn-small"
                  style={{ fontSize: '0.6rem', padding: '4px 8px', background: trackMode === 'ENGINEER' ? 'var(--blue)' : '#333', color: 'white', border: 'none' }}
                  onClick={() => setTrackMode(trackMode === 'SPECTATOR' ? 'ENGINEER' : 'SPECTATOR')}
                >
                  {trackMode === 'SPECTATOR' ? 'VIEW: ENG' : 'VIEW: SPEC'}
                </button>
              </div>
            </div>
            <TrackMap cars={raceState?.cars || []} track={raceState?.track} raceControl={raceState?.race_control} mode={trackMode} />
          </div>

          <div className="panel tower-panel">
            <h2 className="panel-title">LIVE STANDINGS</h2>
            <PositionTower
              cars={raceState?.cars || []}
              onSelectDriver={setSelectedDriver}
              selectedDriver={selectedDriver}
            />
          </div>

          <div className="panel context-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
            <RaceControlStatus raceState={raceState} />
            <PredictionPanel predictions={predictions} raceState={raceState} />
            <AIEngineer raceState={raceState} selectedDriver={selectedDriver} />
            <IncidentPredictor raceState={raceState} />
            <div className="events-wrapper" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', ...(logCollapsed ? {} : { flex: 1 }) }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setLogCollapsed(!logCollapsed)}>
                <h2 className="panel-title" style={{ marginBottom: 0 }}>SCENARIO LOG</h2>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', padding: '2px 8px' }}>{logCollapsed ? '▸ SHOW' : '▾ HIDE'}</span>
              </div>
              {!logCollapsed && <EventLog events={raceState?.events || []} />}
            </div>
          </div>
        </main>

        {/* TELEMETRY VIEW */}
        {(() => {
          const sortedCars = (raceState?.cars || []).slice().sort((a, b) => a.position - b.position)
          const currentCarIdx = sortedCars.findIndex(c => c.driver === selectedDriver)
          const driverAhead = currentCarIdx > 0 ? sortedCars[currentCarIdx - 1] : null

          return (
            <div className="w-full mt-4">
              <TelemetryPanel
                selectedDriver={selectedDriver}
                car={raceState?.cars?.find(c => c.driver === selectedDriver)}
                driverAhead={driverAhead}
                sendCommand={sendDriverCommand}
              />
            </div>
          )
        })()}

        {/* Bottom Controls */}
        {view === 'simulation' && (
          <div className="bottom-panel-container flex flex-col gap-2 fixed bottom-4 left-1/2 -translate-x-1/2 w-[95%] max-w-[1200px] z-50">
            <RaceTimeline
              totalLaps={raceState?.total_laps || 0}
              currentLap={raceState?.lap || 0}
              events={raceState?.events || []}
              onSkipToLap={() => { }}
            />
            <div className="bottom-panel">
              <Controls
                isPlaying={isPlaying}
                onPlay={handlePlay}
                onPause={handlePause}
                onStep={handleStep}
                speed={speed}
                onSpeedChange={handleSpeedChange}
                onRaceControl={handleRaceControl}
                onWeatherControl={handleWeatherControl}
                onSkipToLap={() => { }}
                onSimulateStrategy={() => { }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App