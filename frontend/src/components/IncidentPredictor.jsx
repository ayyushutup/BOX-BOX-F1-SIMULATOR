import React, { useMemo } from 'react'

/**
 * Live incident probability display.
 * Shows SC probability, crash probability, and rain probability
 * based on track data and current race state.
 */
const IncidentPredictor = ({ raceState }) => {
    const predictions = useMemo(() => {
        if (!raceState) return null

        const lap = raceState.lap || 0
        const totalLaps = raceState.total_laps || 78
        const progress = totalLaps > 0 ? lap / totalLaps : 0
        const cars = raceState.cars || []

        // SC probability: base from track + increase mid-race + battles
        let scProb = 0.15 // base
        // More likely in middle of race
        if (progress > 0.2 && progress < 0.7) scProb += 0.1
        // More battles = more incidents
        const battles = cars.filter((c, i) => i > 0 && c.interval !== null && c.interval < 1.0).length
        scProb += battles * 0.03
        // High tire wear increases risk
        const avgWear = cars.reduce((s, c) => s + (c.tire_wear || 0), 0) / Math.max(cars.length, 1)
        if (avgWear > 60) scProb += 0.08
        scProb = Math.min(scProb, 0.95)

        // Rain probability: from track weather if available
        let rainProb = 0.05 // default low
        // We simulate some variation based on lap
        rainProb += Math.sin(progress * Math.PI) * 0.1
        rainProb = Math.max(0.02, Math.min(rainProb, 0.85))

        // Crash probability — correlated with battles and wear
        let crashProb = 0.05
        crashProb += battles * 0.04
        if (avgWear > 70) crashProb += 0.12
        if (raceState.safety_car_active) crashProb -= 0.05
        crashProb = Math.max(0.02, Math.min(crashProb, 0.60))

        return { scProb, rainProb, crashProb }
    }, [raceState?.lap, raceState?.cars])

    const prevRef = React.useRef(null)
    const [trends, setTrends] = React.useState({ scProb: 0, rainProb: 0, crashProb: 0 })

    React.useEffect(() => {
        if (predictions) {
            if (prevRef.current) {
                setTrends({
                    scProb: predictions.scProb - prevRef.current.scProb,
                    rainProb: predictions.rainProb - prevRef.current.rainProb,
                    crashProb: predictions.crashProb - prevRef.current.crashProb,
                })
            }
            prevRef.current = predictions
        }
    }, [predictions])

    if (!predictions) return null

    const items = [
        { label: 'Safety Car', key: 'scProb', prob: predictions.scProb, color: 'var(--yellow)', icon: '🚗' },
        { label: 'Incident', key: 'crashProb', prob: predictions.crashProb, color: 'var(--red)', icon: '⚠️' },
        { label: 'Rain', key: 'rainProb', prob: predictions.rainProb, color: 'var(--blue)', icon: '🌧️' },
    ]

    return (
        <div style={{
            padding: '10px', borderRadius: '8px',
            background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)',
        }}>
            <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '2px', marginBottom: '8px' }}>
                📡 INCIDENT TRENDS
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {items.map(item => {
                    const pct = Math.round(item.prob * 100)
                    const isHigh = item.prob > 0.4
                    const trend = trends[item.key]
                    const trendSymbol = trend > 0.01 ? '↑' : trend < -0.01 ? '↓' : '→'
                    const trendColor = trend > 0.01 ? 'var(--red)' : trend < -0.01 ? 'var(--green)' : 'var(--text-tertiary)'
                    return (
                        <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <span style={{ fontSize: '0.75rem', width: '20px', textAlign: 'center' }}>{item.icon}</span>
                            <span style={{ fontSize: '0.6rem', fontWeight: 600, width: '60px', color: 'var(--text-tertiary)' }}>{item.label}</span>
                            <div style={{ flex: 1, height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{
                                    height: '100%', width: `${pct}%`,
                                    background: item.color, borderRadius: '3px',
                                    transition: 'width 0.5s ease',
                                    boxShadow: isHigh ? `0 0 8px ${item.color}40` : 'none',
                                }} />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', width: '38px' }}>
                                <span style={{
                                    fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700,
                                    color: isHigh ? item.color : 'var(--text-tertiary)', lineHeight: 1
                                }}>{pct}%</span>
                                <span style={{ fontSize: '0.55rem', color: trendColor, fontWeight: 800, marginTop: '2px' }}>
                                    {trendSymbol}
                                </span>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default IncidentPredictor
