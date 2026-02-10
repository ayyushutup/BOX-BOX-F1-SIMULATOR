import { useState, useEffect, useRef, useCallback } from 'react'
import Header from './components/Header'
import TrackMap from './components/TrackMap'
import PositionTower from './components/PositionTower'
import EventLog from './components/EventLog'
import Controls from './components/Controls'
import RaceControlStatus from './components/RaceControlStatus'
import TelemetryPanel from './components/TelemetryPanel'
import TrackSelection from './features/TrackSelection'
import './index.css'

function App() {
  const [view, setView] = useState('dashboard') // 'dashboard' or 'race'
  const [availableTracks, setAvailableTracks] = useState([])
  const [selectedTrackId, setSelectedTrackId] = useState(null)
  const [selectedDriver, setSelectedDriver] = useState(null)
  const [trackMode, setTrackMode] = useState('SPECTATOR') // 'SPECTATOR' | 'ENGINEER'

  const [isConnected, setIsConnected] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [raceState, setRaceState] = useState(null)
  const [speed, setSpeed] = useState(1) // 1x by default
  const wsRef = useRef(null)

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
    // If running, update speed dynamically (optional enhancement for backend)
    // For now, just set state, next 'start' command will pick it up if we toggle logic
    // Or we can send a speed update command if backend supported it.
    // Simpler: restart with new speed
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
      {/* Race View Header with Back Button */}
      <div className="race-controls-header" style={{ position: 'absolute', top: 10, left: 10, zIndex: 100 }}>
        <button className="btn-back" onClick={handleBackToDashboard}>
          ← BACK TO TRACKS
        </button>
      </div>

      <Header
        lap={raceState?.lap || 0}
        totalLaps={raceState?.total_laps || 0}
        time={raceState?.time_ms || 0}
      />

      <main className="main-grid">
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
        <div className="panel context-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <RaceControlStatus raceState={raceState} />

          <div className="events-wrapper" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <h2 className="panel-title">RACE LOG</h2>
            <EventLog events={raceState?.events || []} />
          </div>
        </div>
      </main>

      <div className="bottom-panel">
        <TelemetryPanel
          selectedDriver={selectedDriver}
          car={raceState?.cars?.find(c => c.driver === selectedDriver)}
          sendCommand={sendDriverCommand}
        />
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
        />
      </div>
    </div>
  )
}

export default App