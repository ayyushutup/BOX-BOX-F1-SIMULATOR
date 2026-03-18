import React, { useMemo } from 'react'

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

/**
 * RaceTimelineChart — visualizes lap-by-lap position forecasts 
 * as a position sparkline per driver.
 */
const RaceTimelineChart = ({ predictions, selectedDriver }) => {
    const timeline = predictions?.timeline_forecast?.timeline
    const gapForecast = predictions?.timeline_forecast?.gap_forecast
    const scForecast = predictions?.timeline_forecast?.sc_forecast

    const topDrivers = useMemo(() => {
        if (!timeline) return []
        const drivers = Object.keys(timeline)
        // Sort by initial expected position
        return drivers.sort((a, b) => {
            const aPos = timeline[a]?.[0]?.position_distribution || {}
            const bPos = timeline[b]?.[0]?.position_distribution || {}
            const aAvg = Object.entries(aPos).reduce((s, [k, v]) => s + parseInt(k.replace('P', '')) * v, 0)
            const bAvg = Object.entries(bPos).reduce((s, [k, v]) => s + parseInt(k.replace('P', '')) * v, 0)
            return aAvg - bAvg
        }).slice(0, 6)
    }, [timeline])

    // ALL hooks must be called before any early return (Rules of Hooks)
    const positionLines = useMemo(() => {
        if (!timeline || topDrivers.length === 0) return {}
        const lines = {}
        topDrivers.forEach(driver => {
            lines[driver] = (timeline[driver] || []).map(lapData => {
                const dist = lapData.position_distribution || {}
                return Object.entries(dist).reduce((sum, [pos, prob]) => {
                    return sum + parseInt(pos.replace('P', '')) * prob
                }, 0)
            })
        })
        return lines
    }, [timeline, topDrivers])

    if (!timeline || topDrivers.length === 0) {
        return (
            <div className="panel" style={{ padding: '16px' }}>
                <h2 className="panel-title">RACE TIMELINE FORECAST</h2>
                <div style={{ color: '#555', fontSize: '0.75rem', textAlign: 'center', padding: '24px 0', fontStyle: 'italic' }}>
                    Timeline data will be available after first prediction
                </div>
            </div>
        )
    }

    const laps = timeline[topDrivers[0]]?.map(d => d.lap) || []
    const nDrivers = topDrivers.length

    // SVG dimensions
    const W = 520, H = 160, PAD_L = 28, PAD_R = 12, PAD_T = 8, PAD_B = 20
    const plotW = W - PAD_L - PAD_R
    const plotH = H - PAD_T - PAD_B

    const xScale = (i) => PAD_L + (i / Math.max(1, laps.length - 1)) * plotW
    const yScale = (pos) => PAD_T + ((pos - 1) / Math.max(1, nDrivers)) * plotH

    return (
        <div className="panel" style={{ padding: '16px' }}>
            <h2 className="panel-title">RACE TIMELINE FORECAST</h2>

            {/* Position Sparklines */}
            <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
                {/* Grid lines */}
                {Array.from({ length: nDrivers }, (_, i) => (
                    <line key={`grid-${i}`}
                        x1={PAD_L} y1={yScale(i + 1)} x2={W - PAD_R} y2={yScale(i + 1)}
                        stroke="rgba(255,255,255,0.04)" strokeWidth="1"
                    />
                ))}

                {/* Position labels */}
                {Array.from({ length: Math.min(nDrivers, 6) }, (_, i) => (
                    <text key={`label-${i}`} x={4} y={yScale(i + 1) + 3}
                        fill="#555" fontSize="8" fontFamily="var(--font-mono)">
                        P{i + 1}
                    </text>
                ))}

                {/* Lap labels */}
                {laps.filter((_, i) => i % Math.max(1, Math.floor(laps.length / 6)) === 0).map((lap, i) => (
                    <text key={`lap-${i}`} x={xScale(laps.indexOf(lap))} y={H - 2}
                        fill="#555" fontSize="7" fontFamily="var(--font-mono)" textAnchor="middle">
                        L{lap}
                    </text>
                ))}

                {/* Position lines per driver */}
                {topDrivers.map(driver => {
                    const positions = positionLines[driver] || []
                    if (positions.length < 2) return null
                    const color = TEAM_COLORS[driver] || '#666'
                    const isSelected = driver === selectedDriver
                    const pathData = positions.map((pos, i) => `${i === 0 ? 'M' : 'L'}${xScale(i)},${yScale(pos)}`).join(' ')

                    return (
                        <g key={driver}>
                            <path d={pathData} fill="none" stroke={color}
                                strokeWidth={isSelected ? 2.5 : 1.5}
                                strokeOpacity={isSelected ? 1 : 0.7}
                                style={{ filter: isSelected ? `drop-shadow(0 0 4px ${color})` : 'none' }}
                            />
                            {/* Driver label at end */}
                            <text x={xScale(positions.length - 1) + 4} y={yScale(positions[positions.length - 1]) + 3}
                                fill={color} fontSize="7" fontWeight="700" fontFamily="var(--font-mono)">
                                {driver}
                            </text>
                        </g>
                    )
                })}

                {/* SC probability heat strip */}
                {scForecast && scForecast.map((sc, i) => {
                    if (sc.sc_probability < 0.05) return null
                    return (
                        <rect key={`sc-${i}`}
                            x={xScale(i)} y={PAD_T - 6} width={Math.max(2, plotW / laps.length)} height={4}
                            fill={`rgba(255, 214, 0, ${Math.min(1, sc.sc_probability * 3)})`}
                            rx={1}
                        />
                    )
                })}
            </svg>

            {/* SC legend if any SC probability */}
            {scForecast?.some(s => s.sc_probability > 0.05) && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', fontSize: '0.55rem', color: '#888' }}>
                    <div style={{ width: '12px', height: '4px', borderRadius: '2px', background: 'var(--yellow)' }} />
                    <span>SC PROBABILITY HEAT</span>
                </div>
            )}

            {/* Tire wear mini-table for selected or top 3 */}
            <div style={{ marginTop: '10px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                {topDrivers.slice(0, 3).map(driver => {
                    const tl = timeline[driver] || []
                    const lastPoint = tl[tl.length - 1]
                    const firstPoint = tl[0]
                    const color = TEAM_COLORS[driver] || '#666'
                    const wear = lastPoint?.avg_tire_wear || 0
                    const wearPct = Math.round(wear * 100)
                    const cliff = predictions?.timeline_forecast?.tire_cliff_lap?.[driver]

                    return (
                        <div key={driver} style={{
                            padding: '6px 8px', borderRadius: '6px',
                            background: 'rgba(255,255,255,0.03)',
                            borderLeft: `3px solid ${color}`,
                        }}>
                            <div style={{ fontSize: '0.7rem', fontWeight: 700, color, fontFamily: 'var(--font-mono)' }}>{driver}</div>
                            <div style={{ fontSize: '0.6rem', color: '#888', marginTop: '2px' }}>
                                Wear by L{lastPoint?.lap}: <span style={{ color: wearPct > 75 ? 'var(--red)' : wearPct > 50 ? 'var(--orange)' : 'var(--green)', fontWeight: 700 }}>{wearPct}%</span>
                            </div>
                            {cliff && (
                                <div style={{ fontSize: '0.55rem', color: 'var(--red)', fontWeight: 700, marginTop: '2px' }}>
                                    ⚠ CLIFF L{cliff}
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default RaceTimelineChart
