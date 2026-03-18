import React from 'react'

/**
 * RaceAlerts — displays real-time warnings from timeline forecasting:
 * tire cliff warnings, SC probability windows, and gap closure predictions.
 */
const RaceAlerts = ({ predictions }) => {
    const timeline = predictions?.timeline_forecast
    if (!timeline) return null

    const alerts = []

    // Tire cliff warnings
    const cliffs = timeline.tire_cliff_lap || {}
    Object.entries(cliffs).forEach(([driver, lap]) => {
        alerts.push({
            type: 'cliff',
            severity: 'high',
            icon: '🛞',
            message: `${driver} tire cliff predicted at Lap ${lap}`,
            detail: 'Consider pitting before this lap',
            color: 'var(--red)',
            bg: 'rgba(225, 6, 0, 0.08)',
        })
    })

    // SC probability alerts
    const scForecast = timeline.sc_forecast || []
    const highSC = scForecast.filter(s => s.sc_probability > 0.15)
    if (highSC.length > 0) {
        const maxSC = highSC.reduce((prev, curr) => curr.sc_probability > prev.sc_probability ? curr : prev)
        alerts.push({
            type: 'sc',
            severity: 'medium',
            icon: '🚦',
            message: `SC probability peaks at ${Math.round(maxSC.sc_probability * 100)}% on Lap ${maxSC.lap}`,
            detail: 'Consider gambling on SC pit stop',
            color: 'var(--yellow)',
            bg: 'rgba(255, 214, 0, 0.08)',
        })
    }

    // Gap closure alerts (from gap_forecast)
    const gapForecast = timeline.gap_forecast || {}
    Object.entries(gapForecast).forEach(([pair, data]) => {
        if (data.length < 3) return
        const firstGap = data[0]?.gap || 0
        const lastGap = data[data.length - 1]?.gap || 0
        const closing = firstGap - lastGap

        if (closing > 1.5 && lastGap < 1.0) {
            const [follower, leader] = pair.split('_vs_')
            alerts.push({
                type: 'battle',
                severity: 'low',
                icon: '⚔️',
                message: `${follower} closing on ${leader} — gap ${lastGap.toFixed(1)}s by L${data[data.length - 1]?.lap}`,
                detail: `Closing at ~${(closing / data.length).toFixed(2)}s/lap`,
                color: 'var(--cyan)',
                bg: 'rgba(0, 229, 255, 0.08)',
            })
        }
    })

    if (alerts.length === 0) return null

    // Sort: high severity first
    const severityOrder = { high: 0, medium: 1, low: 2 }
    alerts.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity])

    return (
        <div className="panel" style={{ padding: '14px' }}>
            <h2 className="panel-title">RACE ALERTS</h2>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {alerts.slice(0, 5).map((alert, i) => (
                    <div key={i} style={{
                        display: 'flex', alignItems: 'flex-start', gap: '8px',
                        padding: '8px 10px', borderRadius: '6px',
                        background: alert.bg,
                        borderLeft: `3px solid ${alert.color}`,
                        animation: i === 0 ? 'alertSlide 0.4s ease-out' : 'none',
                    }}>
                        <span style={{ fontSize: '1rem', flexShrink: 0 }}>{alert.icon}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: '0.7rem', fontWeight: 700, color: alert.color }}>
                                {alert.message}
                            </div>
                            <div style={{ fontSize: '0.55rem', color: '#888', marginTop: '1px' }}>
                                {alert.detail}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <style>{`
                @keyframes alertSlide {
                    from { opacity: 0; transform: translateX(-8px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>
        </div>
    )
}

export default RaceAlerts
