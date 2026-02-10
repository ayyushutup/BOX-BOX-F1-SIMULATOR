import { useState } from 'react'

function Controls({ isPlaying, onPlay, onPause, onStep, speed, onSpeedChange, onRaceControl, onWeatherControl, onSkipToLap }) {
    const [skipLap, setSkipLap] = useState('')

    const handleSkip = () => {
        const lap = parseInt(skipLap, 10)
        if (lap > 0 && onSkipToLap) {
            onSkipToLap(lap)
            setSkipLap('')
        }
    }

    return (
        <div className="controls">
            <div className="controls-main">
                <button
                    className={`btn btn-play-large ${isPlaying ? 'playing' : ''}`}
                    onClick={isPlaying ? onPause : onPlay}
                >
                    {isPlaying ? 'PAUSE ⏸' : 'START RACE ▶'}
                </button>
                <button className="btn btn-secondary" onClick={() => onStep(1)}>
                    STEP ⏭
                </button>
            </div>

            <div className="controls-speed">
                <span className="speed-label">SIM SPEED</span>
                <div className="speed-toggles">
                    {[1, 5, 10, 20].map(s => (
                        <button
                            key={s}
                            className={`btn-speed ${speed === s ? 'active' : ''}`}
                            onClick={() => onSpeedChange(s)}
                        >
                            {s}x
                        </button>
                    ))}
                </div>
            </div>

            <div className="controls-skip">
                <span className="speed-label">SKIP TO LAP</span>
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                    <input
                        type="number"
                        min="1"
                        value={skipLap}
                        onChange={(e) => setSkipLap(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSkip()}
                        placeholder="LAP"
                        className="skip-input"
                    />
                    <button className="btn btn-small btn-skip" onClick={handleSkip}>
                        ⏩ GO
                    </button>
                </div>
            </div>

            <div className="controls-director">
                <span className="speed-label" style={{ color: 'var(--red)' }}>RACE DIRECTOR</span>
                <div className="director-buttons">
                    <button className="btn btn-small btn-vsc" onClick={() => onRaceControl('VSC')}>
                        🟡 VSC
                    </button>
                    <button className="btn btn-small btn-sc" onClick={() => onRaceControl('SC')}>
                        🚗 SC
                    </button>
                </div>
                <div className="director-buttons" style={{ marginTop: '8px' }}>
                    <button className="btn btn-small btn-weather-dry" onClick={() => onWeatherControl('DRY')}>
                        ☀️ Dry
                    </button>
                    <button className="btn btn-small btn-weather-rain" onClick={() => onWeatherControl('RAIN')}>
                        🌧️ Rain
                    </button>
                </div>
            </div>
        </div>
    )
}

export default Controls
