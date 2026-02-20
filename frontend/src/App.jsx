import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import TrackMap from './components/TrackMap'
import PositionTower from './components/PositionTower'
import EventLog from './components/EventLog'
import Controls from './components/Controls'
import RaceControlStatus from './components/RaceControlStatus';
import SimVsReality from './components/SimVsReality';
import TelemetryPanel from './components/TelemetryPanel'
import PredictionPanel from './components/PredictionPanel'
import AIEngineer from './components/AIEngineer'
import IncidentPredictor from './components/IncidentPredictor'
import TrackSelection from './features/TrackSelection'
import RaceTimeline from './components/RaceTimeline'
import { useSoundEffects } from './hooks/useSoundEffects'
import './index.css'

function App() {
  const [view, setView] = useState('dashboard') // 'dashboard' or 'race'
  const [raceTab, setRaceTab] = useState('race') // 'race', 'telemetry', 'reality'
  const [availableTracks, setAvailableTracks] = useState([])
  const [selectedTrackId, setSelectedTrackId] = useState(null)
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [trackMode, setTrackMode] = useState('SPECTATOR') // 'SPECTATOR' | 'ENGINEER'

  const [isConnected, setIsConnected] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [raceState, setRaceState] = useState(null)
  const [predictions, setPredictions] = useState(null)
  const [speed, setSpeed] = useState(1)
  const [soundEnabled, setSoundEnabled] = useState(true)
  const [logCollapsed, setLogCollapsed] = useState(true)
  const wsRef = useRef(null)
  const { processEvents } = useSoundEffects(soundEnabled)

  // Fetch available tracks on load
  useEffect(() => {
    fetch('http://localhost:8000/api/tracks')
      .then(res => res.json())
      .then(data => setAvailableTracks(data.tracks))
      .catch(err => console.error("Failed to fetch tracks:", err))
  }, [])

  // Initialize WebSocket connection logic (moved to function for reuse)
  const connectToRace = useCallback((trackId) => {
    if (wsRef.current) {
      wsRef.current.close()
    }

    const ws = new WebSocket('ws://localhost:8000/ws/race')
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Connected to Race Server')
      setIsConnected(true)
      // Initialize race with selected track
      ws.send(JSON.stringify({
        command: 'init',
        track_id: trackId,
        seed: 42,
        laps: trackId === 'spa' ? 44 : trackId === 'monza' ? 53 : trackId === 'silverstone' ? 52 : 78 // Approx laps
      }))
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)

      if (message.type === 'init' || message.type === 'update' || message.type === 'state') {
        setRaceState(message.data)
        // Process sound effects for new events
        if (message.data?.events) {
          processEvents(message.data.events)
        }
        // Extract predictions if piggybacked on update
        if (message.predictions) {
          setPredictions(message.predictions)
        }
      } else if (message.type === 'finished') {
        setRaceState(message.data)
        setIsPlaying(false)
      }
    }

    ws.onclose = () => {
      console.log('Disconnected')
      setIsConnected(false)
      setIsPlaying(false)
    }

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [])

  const handleTrackSelect = (trackId) => {
    setSelectedTrackId(trackId)
    setView('race')
    connectToRace(trackId)
  }

  const handleBackToDashboard = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    setIsPlaying(false)
    setView('dashboard')
    setRaceState(null)
    setPredictions(null)
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
    // If running, update speed dynamically
    if (isPlaying && wsRef.current) {
      wsRef.current.send(JSON.stringify({ command: 'start', speed: newSpeed }))
    }
  }, [isPlaying])

  const handleRaceControl = useCallback((type) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log(`Sending Race Control Command: ${type}`)
      wsRef.current.send(JSON.stringify({ command: 'event', type: type }))
    }
  }, [])

  const handleWeatherControl = useCallback((type) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log(`Sending Weather Control Command: ${type}`)
      wsRef.current.send(JSON.stringify({ command: 'event', type: 'weather', value: type }))
    }
  }, [])

  const handleSkipToLap = useCallback((lap) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log(`Skipping to lap ${lap}`)
      wsRef.current.send(JSON.stringify({ command: 'skip_to_lap', lap }))
    }
  }, [])

  // Team Principal: Send driver command (BOX_THIS_LAP, PUSH, CONSERVE)
  const sendDriverCommand = useCallback((driver, cmd) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command: 'driver_command', driver, cmd }))
      console.log(`[TEAM RADIO] Sent: ${driver} -> ${cmd}`)
    }
  }, [])

  if (view === 'dashboard') {
    return (
      <TrackSelection
        tracks={availableTracks}
        onSelectTrack={handleTrackSelect}
      />
    )
  }

  if (!isConnected && view === 'race') {
    return (
      <div className="app-container connecting-screen">
        <div className="race-loader">
          <h1>ESTABLISHING UPLINK</h1>
          <div className="pulse-bar"></div>
          <p>CONNECTING TO TELEMETRY SERVER ON PORT 8000</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-container">
      {/* Race View Header with Back Button + Sound Toggle */}
      <div className="race-controls-header" style={{ position: 'absolute', top: 10, left: 10, zIndex: 100, display: 'flex', gap: '8px' }}>
        <button className="btn-back" onClick={handleBackToDashboard}>
          ← BACK TO TRACKS
        </button>
        <button
          className="btn-back"
          onClick={() => setSoundEnabled(!soundEnabled)}
          title={soundEnabled ? 'Mute sound effects' : 'Enable sound effects'}
          style={{ minWidth: '36px', textAlign: 'center' }}
        >
          {soundEnabled ? '🔊' : '🔇'}
        </button>
      </div>

      <Header
        lap={raceState?.lap || 0}
        totalLaps={raceState?.total_laps || 0}
        time={raceState?.time_ms || 0}
      />

      {/* TABS CONTAINER */}
      <div className="w-full h-full flex flex-col relative">
        <div style={{ position: 'absolute', top: '10px', right: '20px', zIndex: 50, display: 'flex', gap: '5px', background: 'rgba(0,0,0,0.5)', padding: '5px', borderRadius: '8px' }}>
          <button
            onClick={() => setRaceTab('race')}
            style={{ padding: '5px 10px', borderRadius: '4px', border: 'none', background: raceTab === 'race' ? 'var(--red)' : 'transparent', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Live Race
          </button>
          <button
            onClick={() => setRaceTab('telemetry')}
            style={{ padding: '5px 10px', borderRadius: '4px', border: 'none', background: raceTab === 'telemetry' ? 'var(--red)' : 'transparent', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Telemetry
          </button>
          <button
            onClick={() => setRaceTab('reality')}
            style={{ padding: '5px 10px', borderRadius: '4px', border: 'none', background: raceTab === 'reality' ? 'var(--red)' : 'transparent', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
          >
            Reality Check
          </button>
        </div>

        {/* TAB CONTENTS */}

        {/* VIEW 1: RACE */}
        {raceTab === 'race' && (
          <main className="main-grid w-full h-full pt-12">
            {/* LEFT: Track Awareness */}
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
              <TrackMap cars={raceState?.cars || []} track={raceState?.track} mode={trackMode} />
            </div>

            {/* CENTER: Decision Making */}
            <div className="panel tower-panel">
              <h2 className="panel-title">LIVE STANDINGS</h2>
              <PositionTower
                cars={raceState?.cars || []}
                onSelectDriver={setSelectedDriver}
                selectedDriver={selectedDriver}
              />
            </div>

            {/* RIGHT: Context & Safety */}
            <div className="panel context-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
              <RaceControlStatus raceState={raceState} />
              <PredictionPanel predictions={predictions} raceState={raceState} />
              <AIEngineer raceState={raceState} selectedDriver={selectedDriver} />
              <IncidentPredictor raceState={raceState} />

              <div className="events-wrapper" style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column', ...(logCollapsed ? {} : { flex: 1 }) }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setLogCollapsed(!logCollapsed)}>
                  <h2 className="panel-title" style={{ marginBottom: 0 }}>RACE LOG</h2>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', padding: '2px 8px' }}>{logCollapsed ? '▸ SHOW' : '▾ HIDE'}</span>
                </div>
                {!logCollapsed && <EventLog events={raceState?.events || []} />}
              </div>
            </div>
          </main>
        )}

        {/* VIEW 2: TELEMETRY */}
        {raceTab === 'telemetry' && (
          <div className="w-full h-full pt-12 p-4">
            <TelemetryPanel
              selectedDriver={selectedDriver}
              car={raceState?.cars?.find(c => c.driver === selectedDriver)}
              sendCommand={sendDriverCommand}
            />
          </div>
        )}

        {/* VIEW 3: REALITY CHECK */}
        {raceTab === 'reality' && (
          <div className="w-full h-full pt-12 p-4 overflow-auto">
            <SimVsReality />
          </div>
        )}


        {/* Global Bottom Controls (Always visible in Race/Telemetry views) */}
        {view === 'race' && raceTab !== 'reality' && (
          <div className="bottom-panel-container flex flex-col gap-2 fixed bottom-4 left-1/2 -translate-x-1/2 w-[95%] max-w-[1200px] z-50">
            <RaceTimeline
              totalLaps={raceState?.total_laps || 0}
              currentLap={raceState?.lap || 0}
              events={raceState?.events || []}
              onSkipToLap={handleSkipToLap}
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
                onSkipToLap={handleSkipToLap}
                onSimulateStrategy={() => console.log("Strategy Sim Open")} // Placeholder for future
              />
            </div>
          </div>
        )}
      </div>

    </div>
  )
}

export default App