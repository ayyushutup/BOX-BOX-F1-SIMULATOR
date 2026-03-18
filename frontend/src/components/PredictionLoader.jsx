import React, { useState, useEffect } from 'react'

const STAGES = [
    { label: 'KALMAN FILTER', icon: '🔬', detail: 'Correcting hidden state...' },
    { label: 'FEATURE ENGINE', icon: '⚡', detail: 'Building driver features...' },
    { label: 'ML INFERENCE', icon: '🧠', detail: 'LightGBM + PPO models...' },
    { label: 'MONTE CARLO', icon: '🎲', detail: '500 race simulations...' },
    { label: 'STRATEGY AI', icon: '🏎️', detail: 'Optimizing pit windows...' },
    { label: 'TIMELINE FORECAST', icon: '📊', detail: 'Lap-by-lap projection...' },
    { label: 'COMMENTARY', icon: '🎙️', detail: 'Generating AI analysis...' },
]

/**
 * PredictionLoader — animated loading overlay shown during prediction computation.
 * Cycles through pipeline stages to show progress.
 */
const PredictionLoader = ({ isLoading }) => {
    const [stageIndex, setStageIndex] = useState(0)
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        if (!isLoading) {
            setStageIndex(0)
            setProgress(0)
            return
        }

        // Cycle through stages
        const stageInterval = setInterval(() => {
            setStageIndex(prev => (prev + 1) % STAGES.length)
        }, 200)

        // Smooth progress bar
        const progressInterval = setInterval(() => {
            setProgress(prev => {
                if (prev >= 95) return prev // Hold at 95% until complete
                return prev + (95 - prev) * 0.08 // Ease towards 95%
            })
        }, 50)

        return () => {
            clearInterval(stageInterval)
            clearInterval(progressInterval)
        }
    }, [isLoading])

    if (!isLoading) return null

    const stage = STAGES[stageIndex]

    return (
        <div style={{
            position: 'fixed', inset: 0, zIndex: 9999,
            background: 'rgba(7, 8, 10, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            animation: 'loaderFadeIn 0.3s ease',
        }}>
            {/* Spinning ring */}
            <div style={{
                width: '80px', height: '80px', borderRadius: '50%',
                border: '3px solid rgba(225, 6, 0, 0.15)',
                borderTopColor: 'var(--red)',
                animation: 'loaderSpin 0.8s linear infinite',
                marginBottom: '24px',
                boxShadow: '0 0 20px rgba(225, 6, 0, 0.2)',
            }} />

            {/* Stage label */}
            <div style={{
                fontSize: '0.7rem', fontFamily: 'var(--font-display)',
                letterSpacing: '3px', color: 'var(--red)',
                marginBottom: '6px', fontWeight: 700,
            }}>
                PREDICTION ENGINE
            </div>

            {/* Current stage */}
            <div style={{
                display: 'flex', alignItems: 'center', gap: '8px',
                fontSize: '1rem', fontWeight: 700, color: '#fff',
                marginBottom: '4px',
                animation: 'loaderPulse 0.2s ease',
                key: stageIndex,
            }}>
                <span>{stage.icon}</span>
                <span style={{ fontFamily: 'var(--font-mono)', letterSpacing: '1px' }}>
                    {stage.label}
                </span>
            </div>

            <div style={{ fontSize: '0.65rem', color: '#888', marginBottom: '20px' }}>
                {stage.detail}
            </div>

            {/* Progress bar */}
            <div style={{
                width: '240px', height: '3px', borderRadius: '2px',
                background: 'rgba(255,255,255,0.06)', overflow: 'hidden',
            }}>
                <div style={{
                    height: '100%', borderRadius: '2px',
                    background: 'linear-gradient(90deg, var(--red), var(--orange))',
                    width: `${progress}%`,
                    transition: 'width 0.1s ease',
                    boxShadow: '0 0 8px rgba(225, 6, 0, 0.4)',
                }} />
            </div>

            <div style={{
                marginTop: '8px', fontSize: '0.55rem', fontFamily: 'var(--font-mono)',
                color: '#555',
            }}>
                {Math.round(progress)}%
            </div>

            <style>{`
                @keyframes loaderSpin {
                    to { transform: rotate(360deg); }
                }
                @keyframes loaderFadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes loaderPulse {
                    from { opacity: 0.5; transform: translateY(4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    )
}

export default PredictionLoader
