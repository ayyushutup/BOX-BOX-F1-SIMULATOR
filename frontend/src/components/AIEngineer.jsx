import React, { useMemo } from 'react'

/**
 * AI Race Engineer — generates contextual strategic advice
 * based on current race state. Pure client-side heuristics.
 */
const AIEngineer = ({ raceState, selectedDriver }) => {
    const messages = useMemo(() => {
        if (!raceState || !raceState.cars?.length) return []
        const msgs = []
        const cars = raceState.cars

        // Find the selected driver's car (or leader)
        const targetDriver = selectedDriver || cars[0]?.driver
        const car = cars.find(c => c.driver === targetDriver) || cars[0]
        if (!car) return []

        const sorted = [...cars].sort((a, b) => a.position - b.position)
        const carIdx = sorted.findIndex(c => c.driver === car.driver)

        // 1. Tire degradation warning
        const wear = car.tire_wear || 0
        if (wear > 80) {
            msgs.push({ icon: '🛞', text: `Critical tyre wear (${wear.toFixed(0)}%). Box box this lap.`, priority: 'critical' })
        } else if (wear > 60) {
            msgs.push({ icon: '🛞', text: `Tyres degrading (${wear.toFixed(0)}%). Consider pit window.`, priority: 'warning' })
        }

        // 2. Undercut/overcut opportunity
        if (carIdx > 0 && carIdx < sorted.length) {
            const ahead = sorted[carIdx - 1]
            const gapAhead = car.interval
            if (gapAhead && gapAhead < 2.0 && gapAhead > 0.5 && wear > 40) {
                msgs.push({ icon: '⚡', text: `Undercut window on ${ahead.driver}. Gap: ${gapAhead.toFixed(1)}s. Box for fresh tyres.`, priority: 'info' })
            }
        }

        // 3. DRS opportunity
        if (carIdx > 0) {
            const ahead = sorted[carIdx - 1]
            const gap = car.interval
            if (gap && gap < 1.0 && !car.drs_active) {
                msgs.push({ icon: '🏎️', text: `DRS range to ${ahead.driver} (${gap.toFixed(1)}s). Push for activation.`, priority: 'info' })
            }
        }

        // 4. Fuel management
        const fuel = car.fuel ?? 100
        const lapsRemaining = (raceState.total_laps || 78) - (raceState.lap || 0)
        if (lapsRemaining > 0) {
            const fuelPerLap = fuel / lapsRemaining
            if (fuelPerLap < 1.2 && lapsRemaining > 5) {
                msgs.push({ icon: '⛽', text: `Fuel critical. ${fuel.toFixed(1)}kg for ${lapsRemaining} laps. Lift and coast.`, priority: 'warning' })
            }
        }

        // 5. ERS deploy advice
        const ers = car.ers_battery ?? 4
        if (ers > 3.0 && carIdx > 0) {
            const ahead = sorted[carIdx - 1]
            msgs.push({ icon: '⚡', text: `ERS battery high (${((ers / 4) * 100).toFixed(0)}%). Deploy for overtake on ${ahead.driver}.`, priority: 'info' })
        }

        // 6. Safety car restart
        if (raceState.safety_car_active || raceState.vsc_active) {
            msgs.push({ icon: '🟡', text: 'Safety car active. Prepare for restart — warm tyres and brakes.', priority: 'warning' })
        }

        // 7. Position defense
        if (carIdx < sorted.length - 1) {
            const behind = sorted[carIdx + 1]
            const gapBehind = behind?.interval
            if (gapBehind && gapBehind < 0.8) {
                msgs.push({ icon: '🛡️', text: `${behind.driver} closing fast (-${gapBehind.toFixed(1)}s). Defend position.`, priority: 'warning' })
            }
        }

        // Default if no alerts
        if (msgs.length === 0) {
            msgs.push({ icon: '✅', text: 'All systems nominal. Maintain pace.', priority: 'ok' })
        }

        return msgs.slice(0, 4) // Max 4 messages
    }, [raceState?.lap, raceState?.cars, selectedDriver])

    if (!raceState) return null

    const priorityColors = {
        critical: { bg: 'rgba(255,50,50,0.08)', border: 'rgba(255,50,50,0.25)', text: '#ff6b6b' },
        warning: { bg: 'rgba(255,200,0,0.08)', border: 'rgba(255,200,0,0.2)', text: '#ffc800' },
        info: { bg: 'rgba(0,229,255,0.06)', border: 'rgba(0,229,255,0.15)', text: 'var(--cyan)' },
        ok: { bg: 'rgba(0,220,100,0.06)', border: 'rgba(0,220,100,0.15)', text: 'var(--green)' },
    }

    return (
        <div style={{
            padding: '10px', borderRadius: '8px',
            background: 'rgba(0,0,0,0.4)', border: '1px solid var(--glass-border)',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--cyan)', letterSpacing: '2px' }}>🎧 RACE ENGINEER</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {messages.map((msg, i) => {
                    const colors = priorityColors[msg.priority] || priorityColors.info
                    return (
                        <div key={i} style={{
                            display: 'flex', alignItems: 'flex-start', gap: '6px',
                            padding: '6px 8px', borderRadius: '5px',
                            background: colors.bg, borderLeft: `2px solid ${colors.border}`,
                            fontSize: '0.68rem', color: colors.text,
                            fontFamily: 'var(--font-main)',
                            animation: i === 0 ? 'fade-in 0.3s ease' : 'none',
                        }}>
                            <span style={{ flexShrink: 0 }}>{msg.icon}</span>
                            <span style={{ lineHeight: 1.4 }}>{msg.text}</span>
                        </div>
                    )
                })}
            </div>
            <style>{`
                @keyframes fade-in {
                    from { opacity: 0; transform: translateX(-4px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>
        </div>
    )
}

export default AIEngineer
