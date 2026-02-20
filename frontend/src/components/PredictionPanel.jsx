import React, { useRef, useMemo, useState } from 'react'
import ConfidenceCurve from './ConfidenceCurve'

const TEAM_COLORS = {
    'VER': '#3671C6', 'PER': '#3671C6',
    'HAM': '#6CD3BF', 'RUS': '#6CD3BF',
    'LEC': '#F91536', 'SAI': '#F91536',
    'NOR': '#F58020', 'PIA': '#F58020',
    'ALO': '#358C75', 'STR': '#358C75',
    'GAS': '#2293D1', 'OCO': '#2293D1',
    'HUL': '#B6BABD', 'MAG': '#B6BABD',
    'TSU': '#6692FF', 'RIC': '#6692FF',
    'ALB': '#64C4FF', 'SAR': '#64C4FF',
    'BOT': '#52E252', 'ZHO': '#52E252',
}

const PredictionPanel = ({ predictions, raceState }) => {
    const prevPredRef = useRef(null)
    const [isRetraining, setIsRetraining] = useState(false)

    const deltas = useMemo(() => {
        if (!predictions || !prevPredRef.current) return {}
        const prev = prevPredRef.current
        const d = {}
        for (const [driver, prob] of Object.entries(predictions.win_prob || {})) {
            const prevProb = prev.win_prob?.[driver] ?? prob
            d[driver] = prob - prevProb
        }
        return d
    }, [predictions])

    if (predictions && predictions !== prevPredRef.current) {
        setTimeout(() => { prevPredRef.current = predictions }, 1500)
    }

    if (!raceState) return null

    const confidence = predictions?.confidence

    const handleRetrain = async () => {
        try {
            setIsRetraining(true)
            await fetch('http://localhost:8000/api/ml/retrain', { method: 'POST' })
            setTimeout(() => setIsRetraining(false), 2000)
        } catch (e) {
            console.error("Retrain failed", e)
            setIsRetraining(false)
        }
    }

    return (
        <div className="panel prediction-panel">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #2a2a2a', paddingBottom: '8px', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <h2 className="panel-title" style={{ marginBottom: 0, paddingBottom: 0, borderBottom: 'none' }}>AI STRATEGY INSIGHTS</h2>
                    <button
                        style={{
                            background: isRetraining ? 'rgba(0,220,100,0.1)' : 'transparent',
                            border: `1px solid ${isRetraining ? '#00dc64' : '#444'}`,
                            color: isRetraining ? '#00dc64' : '#aaa',
                            fontSize: '0.6rem', padding: '3px 8px', borderRadius: '4px',
                            cursor: isRetraining ? 'not-allowed' : 'pointer',
                            fontFamily: 'var(--font-mono)', transition: 'all 0.2s',
                            opacity: isRetraining ? 0.7 : 1
                        }}
                        onClick={handleRetrain}
                        disabled={isRetraining}
                    >
                        {isRetraining ? '⟳ TRAINING...' : '🧠 RETRAIN'}
                    </button>
                </div>
                {confidence !== undefined && (
                    <div style={{
                        fontSize: '0.8rem', fontWeight: 700, padding: '3px 10px', borderRadius: '6px',
                        fontFamily: 'var(--font-mono)',
                        background: confidence > 0.7 ? 'rgba(0,220,100,0.12)' : confidence > 0.4 ? 'rgba(255,200,0,0.12)' : 'rgba(255,60,60,0.12)',
                        color: confidence > 0.7 ? '#00dc64' : confidence > 0.4 ? '#ffc800' : '#ff6b6b',
                        border: `1px solid ${confidence > 0.7 ? 'rgba(0,220,100,0.25)' : confidence > 0.4 ? 'rgba(255,200,0,0.25)' : 'rgba(255,60,60,0.25)'}`,
                    }}>
                        {Math.round(confidence * 100)}% CONF
                    </div>
                )}
            </div>

            {/* Content */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {!predictions ? (
                    <div style={{ color: '#555', fontSize: '0.75rem', textAlign: 'center', padding: '16px 0', position: 'relative', overflow: 'hidden' }}>
                        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, transparent, rgba(0,200,255,0.4), transparent)', animation: 'scan 2s linear infinite' }} />
                        GATHERING TELEMETRY FOR AI...
                    </div>
                ) : (
                    <>
                        {/* Win Probability List — uses MC distribution when available */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: '#555', letterSpacing: '0.05em', marginBottom: '2px' }}>
                            <span>DRIVER</span>
                            <span>{predictions.mc_win_distribution ? 'MC WIN PROBABILITY' : 'WIN PROBABILITY'}</span>
                        </div>

                        {(() => {
                            const winSource = predictions.mc_win_distribution || predictions.win_prob || {}
                            return Object.entries(winSource)
                                .sort(([, a], [, b]) => b - a)
                                .slice(0, 5)
                                .map(([driver, prob], index) => {
                                    const delta = deltas[driver] || 0
                                    const absDelta = Math.abs(delta * 100)
                                    const showDelta = absDelta > 0.3
                                    const teamColor = TEAM_COLORS[driver] || '#666'
                                    const isTopDriver = index === 0

                                    return (
                                        <div key={driver} style={{
                                            display: 'flex', alignItems: 'center', gap: '8px',
                                            fontFamily: 'var(--font-mono)',
                                            padding: isTopDriver ? '6px 8px' : '3px 6px',
                                            borderRadius: '6px',
                                            background: isTopDriver ? 'rgba(255,255,255,0.04)' : 'transparent',
                                            borderLeft: isTopDriver ? `3px solid ${teamColor}` : '3px solid transparent',
                                            transition: 'background 0.3s',
                                            ...(showDelta ? { animation: 'highlight-shift 1.5s ease-out' } : {}),
                                        }}>
                                            <span style={{
                                                fontWeight: 700, width: '32px',
                                                fontSize: isTopDriver ? '0.95rem' : '0.78rem',
                                                color: isTopDriver ? 'white' : 'var(--text-primary)',
                                            }}>{driver}</span>

                                            <div style={{
                                                width: '6px', height: '6px', borderRadius: '50%',
                                                background: teamColor, boxShadow: `0 0 6px ${teamColor}40`,
                                                flexShrink: 0,
                                            }} />

                                            <div style={{ flex: 1, height: isTopDriver ? '10px' : '7px', background: '#1a1a1a', borderRadius: '3px', overflow: 'hidden' }}>
                                                <div style={{
                                                    height: '100%', width: `${Math.min(prob * 100, 100)}%`,
                                                    background: `linear-gradient(90deg, ${teamColor}88, ${teamColor})`,
                                                    borderRadius: '3px', transition: 'width 0.6s ease-out',
                                                    boxShadow: isTopDriver ? `0 0 8px ${teamColor}40` : 'none',
                                                }} />
                                            </div>

                                            <span style={{
                                                fontSize: isTopDriver ? '0.85rem' : '0.72rem',
                                                width: '42px', textAlign: 'right',
                                                color: isTopDriver ? 'white' : '#ccc',
                                                fontWeight: isTopDriver ? 700 : 400,
                                            }}>{(prob * 100).toFixed(1)}%</span>

                                            {showDelta && (
                                                <span style={{
                                                    fontSize: '0.55rem', width: '32px', textAlign: 'right', fontWeight: 700,
                                                    color: delta > 0 ? '#00dc64' : '#ff4444',
                                                    animation: 'fade-in 0.3s ease',
                                                }}>
                                                    {delta > 0 ? '▲' : '▼'}{absDelta.toFixed(1)}
                                                </span>
                                            )}
                                        </div>
                                    )
                                })
                        })()}

                        {/* Predicted Finish Order — from Monte Carlo */}
                        {predictions.predicted_order && predictions.predicted_order.length > 0 && (
                            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #222' }}>
                                <div style={{ fontSize: '0.6rem', color: '#555', letterSpacing: '0.05em', marginBottom: '4px' }}>🏁 PREDICTED FINISH ORDER</div>
                                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                                    {predictions.predicted_order.slice(0, 5).map((driver, idx) => {
                                        const medals = ['🥇', '🥈', '🥉']
                                        const teamColor = TEAM_COLORS[driver] || '#666'
                                        return (
                                            <div key={driver} style={{
                                                display: 'flex', gap: '4px', alignItems: 'center',
                                                background: idx < 3 ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
                                                padding: '3px 8px', borderRadius: '4px',
                                                fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
                                                borderLeft: `2px solid ${teamColor}`,
                                            }}>
                                                <span style={{ fontSize: '0.65rem' }}>{medals[idx] || `P${idx + 1}`}</span>
                                                <span style={{ fontWeight: 700, color: idx < 3 ? '#fff' : '#aaa' }}>{driver}</span>
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}

                        {/* Podium Row */}
                        {predictions.podium_prob && (
                            <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #222' }}>
                                <div style={{ fontSize: '0.6rem', color: '#555', letterSpacing: '0.05em', marginBottom: '4px' }}>PODIUM %</div>
                                <div style={{ display: 'flex', gap: '6px' }}>
                                    {Object.entries(predictions.podium_prob)
                                        .sort(([, a], [, b]) => b - a)
                                        .slice(0, 3)
                                        .map(([driver, prob]) => (
                                            <div key={driver} style={{
                                                display: 'flex', gap: '4px', alignItems: 'center',
                                                background: 'rgba(255,255,255,0.04)', padding: '3px 10px', borderRadius: '4px',
                                                fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
                                                borderLeft: `2px solid ${TEAM_COLORS[driver] || '#666'}`
                                            }}>
                                                <span style={{ fontWeight: 700, color: '#aaa' }}>{driver}</span>
                                                <span style={{ color: '#ffc800', fontWeight: 700 }}>{(prob * 100).toFixed(0)}%</span>
                                            </div>
                                        ))}
                                </div>
                            </div>
                        )}

                        {/* Confidence Curve */}
                        <div style={{ marginTop: '4px' }}>
                            <ConfidenceCurve isPlaying={raceState?.is_finished === false} />
                        </div>
                    </>
                )}
            </div>

            <style>{`
                @keyframes scan {
                    from { transform: translateX(-100%); }
                    to { transform: translateX(100%); }
                }
                @keyframes highlight-shift {
                    0% { background: rgba(255,255,255,0.06); }
                    100% { background: transparent; }
                }
                @keyframes fade-in {
                    from { opacity: 0; transform: translateY(4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    )
}

export default PredictionPanel
