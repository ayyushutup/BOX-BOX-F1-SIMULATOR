import React from 'react'

const TEAM_COLORS = {
    'VER': '#3671C6', 'PER': '#3671C6',
    'HAM': '#6CD3BF', 'RUS': '#6CD3BF',
    'LEC': '#F91536', 'SAI': '#F91536',
    'NOR': '#F58020', 'PIA': '#F58020',
    'ALO': '#358C75', 'STR': '#358C75',
    'GAS': '#2293D1', 'OCO': '#2293D1',
}

/**
 * StateEstimationCard — displays Kalman-corrected hidden state estimates
 * for a selected driver: tire wear, fuel, pace offset, reliability.
 */
const StateEstimationCard = ({ predictions, selectedDriver }) => {
    const states = predictions?.corrected_states
    const paceCorrections = predictions?.pace_corrections

    if (!states || Object.keys(states).length === 0) {
        return null // Don't render if no data — save space
    }

    const driverKey = selectedDriver && states[selectedDriver] ? selectedDriver : Object.keys(states)[0]
    const s = states[driverKey]
    if (!s) return null

    const paceCorr = paceCorrections?.[driverKey] || 0
    const color = TEAM_COLORS[driverKey] || '#888'

    // Helper gauge
    const Gauge = ({ label, value, max, unit, color: gaugeColor, warning }) => {
        const pct = Math.min(100, (value / max) * 100)
        return (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.55rem' }}>
                    <span style={{ color: '#888', letterSpacing: '0.5px' }}>{label}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: warning ? 'var(--red)' : '#ccc' }}>
                        {typeof value === 'number' ? value.toFixed(value < 10 ? 2 : 1) : value}{unit}
                    </span>
                </div>
                <div style={{ height: '3px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{
                        height: '100%', width: `${pct}%`, borderRadius: '2px',
                        background: warning ? 'var(--red)' : gaugeColor,
                        transition: 'width 0.5s ease',
                    }} />
                </div>
            </div>
        )
    }

    return (
        <div className="panel" style={{ padding: '14px' }}>
            <h2 className="panel-title">STATE ESTIMATION</h2>

            {/* Driver selector */}
            <div style={{ display: 'flex', gap: '4px', marginBottom: '10px', flexWrap: 'wrap' }}>
                {Object.keys(states).slice(0, 6).map(d => (
                    <span key={d} style={{
                        fontSize: '0.6rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                        padding: '2px 6px', borderRadius: '3px', cursor: 'default',
                        background: d === driverKey ? (TEAM_COLORS[d] || '#555') : 'rgba(255,255,255,0.05)',
                        color: d === driverKey ? '#000' : '#888',
                    }}>
                        {d}
                    </span>
                ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <Gauge label="TIRE WEAR" value={s.tire_wear * 100} max={100} unit="%"
                    color="var(--orange)" warning={s.tire_wear > 0.75} />
                <Gauge label="TIRE TEMP" value={s.tire_temp} max={150} unit="°C"
                    color="var(--red)" warning={s.tire_temp > 120} />
                <Gauge label="FUEL LOAD" value={s.fuel_load} max={110} unit=" kg"
                    color="var(--cyan)" warning={s.fuel_load < 5} />
                <Gauge label="RELIABILITY" value={s.reliability * 100} max={100} unit="%"
                    color="var(--green)" warning={s.reliability < 0.9} />
            </div>

            {/* Pace correction */}
            <div style={{
                marginTop: '10px', padding: '6px 10px', borderRadius: '6px',
                background: Math.abs(paceCorr) > 0.1 ? (paceCorr < 0 ? 'rgba(0,230,118,0.08)' : 'rgba(255,60,60,0.08)') : 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.06)',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
                <span style={{ fontSize: '0.6rem', color: '#888', letterSpacing: '0.5px' }}>KALMAN PACE CORRECTION</span>
                <span style={{
                    fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                    color: paceCorr < -0.1 ? 'var(--green)' : paceCorr > 0.1 ? 'var(--red)' : '#aaa',
                }}>
                    {paceCorr > 0 ? '+' : ''}{paceCorr.toFixed(2)}s
                </span>
            </div>

            {/* Uncertainty indicator */}
            <div style={{ marginTop: '6px', fontSize: '0.5rem', color: '#555', fontFamily: 'var(--font-mono)', display: 'flex', gap: '12px' }}>
                <span>σ_wear: ±{((s.tire_wear_uncertainty || 0) * 100).toFixed(1)}%</span>
                <span>σ_pace: ±{(s.pace_offset_uncertainty || 0).toFixed(2)}s</span>
                <span>σ_rel: ±{((s.reliability_uncertainty || 0) * 100).toFixed(1)}%</span>
            </div>
        </div>
    )
}

export default StateEstimationCard
