import React from 'react'

const COMPOUND_COLORS = {
    'SOFT': '#ff3333',
    'MEDIUM': '#ffd700',
    'HARD': '#eeeeee',
    'INTERMEDIATE': '#00cc44',
    'WET': '#0088ff',
}

/**
 * StrategyRecommendation — shows optimal pit strategy, pit window,
 * compound sequence, and stop-count comparison for a selected driver.
 */
const StrategyRecommendation = ({ predictions, selectedDriver }) => {
    const allStrats = predictions?.strategy_recommendations
    if (!allStrats || Object.keys(allStrats).length === 0) {
        return (
            <div className="panel" style={{ padding: '14px' }}>
                <h2 className="panel-title">PIT STRATEGY AI</h2>
                <div style={{ color: '#555', fontSize: '0.7rem', textAlign: 'center', padding: '12px 0', fontStyle: 'italic' }}>
                    Strategy recommendations loading...
                </div>
            </div>
        )
    }

    // Show selected driver's strategy, or the first available
    const driverKey = selectedDriver && allStrats[selectedDriver] ? selectedDriver : Object.keys(allStrats)[0]
    const strat = allStrats[driverKey]
    if (!strat) return null

    const best = strat.recommended_strategy
    const comparison = strat.stop_count_comparison || {}
    const pitWindow = strat.pit_window || 'N/A'
    const topStrategies = strat.all_strategies || []

    return (
        <div className="panel" style={{ padding: '14px' }}>
            <h2 className="panel-title">PIT STRATEGY AI</h2>

            {/* Driver selector tabs */}
            <div style={{ display: 'flex', gap: '4px', marginBottom: '10px', flexWrap: 'wrap' }}>
                {Object.keys(allStrats).slice(0, 5).map(d => (
                    <span key={d} style={{
                        fontSize: '0.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                        padding: '2px 8px', borderRadius: '3px', cursor: 'default',
                        background: d === driverKey ? 'var(--cyan)' : 'rgba(255,255,255,0.05)',
                        color: d === driverKey ? '#000' : '#888',
                    }}>
                        {d}
                    </span>
                ))}
            </div>

            {/* Recommended Strategy */}
            {best && (
                <div style={{
                    padding: '10px 12px', borderRadius: '8px', marginBottom: '10px',
                    background: 'linear-gradient(135deg, rgba(0,229,255,0.08), rgba(0,230,118,0.06))',
                    border: '1px solid rgba(0,229,255,0.2)',
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <span style={{ fontSize: '0.6rem', color: 'var(--cyan)', fontWeight: 700, letterSpacing: '1px' }}>
                            ★ OPTIMAL STRATEGY
                        </span>
                        <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#aaa' }}>
                            {best.total_time_cost}s cost
                        </span>
                    </div>

                    {/* Compound sequence */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '6px' }}>
                        {best.compounds.map((c, i) => (
                            <React.Fragment key={i}>
                                <div style={{
                                    width: '20px', height: '20px', borderRadius: '50%',
                                    background: COMPOUND_COLORS[c] || '#666',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: '0.5rem', fontWeight: 700, color: c === 'HARD' ? '#000' : '#fff',
                                    boxShadow: `0 0 6px ${COMPOUND_COLORS[c]}40`,
                                }}>
                                    {c[0]}
                                </div>
                                {i < best.compounds.length - 1 && (
                                    <span style={{ color: '#555', fontSize: '0.7rem' }}>→</span>
                                )}
                            </React.Fragment>
                        ))}
                        <span style={{ marginLeft: '8px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#ccc', fontWeight: 600 }}>
                            {best.label}
                        </span>
                    </div>

                    {/* Pit window */}
                    <div style={{ fontSize: '0.6rem', color: '#888' }}>
                        <span style={{ color: 'var(--green)', fontWeight: 700 }}>PIT WINDOW:</span>{' '}
                        <span style={{ fontFamily: 'var(--font-mono)', color: '#ccc' }}>{pitWindow}</span>
                    </div>
                </div>
            )}

            {/* Stop count comparison */}
            <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '0.55rem', color: '#666', letterSpacing: '1px', marginBottom: '4px' }}>
                    STOP COUNT COMPARISON
                </div>
                <div style={{ display: 'flex', gap: '6px' }}>
                    {Object.entries(comparison).sort((a, b) => a[1] - b[1]).map(([key, time]) => {
                        const isBest = best && time === best.total_time_cost
                        return (
                            <div key={key} style={{
                                flex: 1, padding: '6px 8px', borderRadius: '6px',
                                background: isBest ? 'rgba(0,230,118,0.08)' : 'rgba(255,255,255,0.03)',
                                border: isBest ? '1px solid rgba(0,230,118,0.3)' : '1px solid transparent',
                                textAlign: 'center',
                            }}>
                                <div style={{ fontSize: '0.6rem', color: '#888', fontFamily: 'var(--font-mono)' }}>
                                    {key.replace('_', '-')}
                                </div>
                                <div style={{
                                    fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                                    color: isBest ? 'var(--green)' : '#aaa',
                                }}>
                                    {time}s
                                </div>
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Top alternatives */}
            {topStrategies.length > 1 && (
                <div>
                    <div style={{ fontSize: '0.55rem', color: '#666', letterSpacing: '1px', marginBottom: '4px' }}>
                        ALTERNATIVES
                    </div>
                    {topStrategies.slice(1, 4).map((s, i) => (
                        <div key={i} style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            padding: '3px 6px', fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
                            color: '#888', borderBottom: '1px solid rgba(255,255,255,0.03)',
                        }}>
                            <span>{s.label}</span>
                            <span style={{ color: '#aaa' }}>+{(s.total_time - best.total_time_cost).toFixed(1)}s</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default StrategyRecommendation
