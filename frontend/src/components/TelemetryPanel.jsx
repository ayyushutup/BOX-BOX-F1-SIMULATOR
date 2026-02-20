import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts'

const TelemetryPanel = ({ selectedDriver, car, driverAhead, sendCommand }) => {
    const [rpmHistory, setRpmHistory] = useState([])
    const [speedDelta, setSpeedDelta] = useState(0)
    const [lastSpeed, setLastSpeed] = useState(0)
    const tickRef = useRef(0)

    // Compute telemetry from car data (pure — no side effects)
    const simulatedTelemetry = useMemo(() => {
        if (!car) return { gear: 1, rpm: 4000, throttle: 0, brake: 0, drs: false, steering: 0, tireTemps: [80, 80, 80, 80] }

        const speed = car.speed || 0
        const gear = speed <= 0 ? 1 : Math.min(8, Math.max(1, Math.ceil(speed / 40)))
        const gearBaseSpeed = (gear - 1) * 40
        const gearRange = 40
        const gearProgress = gearRange > 0 ? Math.max(0, Math.min(1, (speed - gearBaseSpeed) / gearRange)) : 0
        const rpm = 4000 + (gearProgress * 8500)
        const clampedRpm = Math.min(12500, Math.max(4000, rpm))

        const throttle = speed > 50 ? (90 + (Math.random() * 10)) : (Math.random() * 50)
        const brake = speed < 100 && speed > 0 ? (Math.random() * 80) : 0

        return {
            gear,
            rpm: clampedRpm,
            throttle,
            brake,
            drs: car.drs_active || false,
            tireTemps: [90 + Math.random() * 10, 90 + Math.random() * 10, 80 + Math.random() * 10, 80 + Math.random() * 10]
        }
    }, [car?.speed, car?.drs_active, car?.lap_progress])

    // RPM history — side effect goes in useEffect
    useEffect(() => {
        if (!car) return
        tickRef.current++
        setRpmHistory(prev => {
            const next = [...prev, { t: tickRef.current, rpm: Math.round(simulatedTelemetry.rpm) }]
            return next.length > 60 ? next.slice(-60) : next
        })

        // Speed delta calculation for micro animation
        setLastSpeed(prev => {
            const currentSpeed = Math.round(car?.speed || 0)
            if (currentSpeed !== prev) {
                setSpeedDelta(Math.round(currentSpeed - prev))
            }
            return currentSpeed
        })
    }, [car?.speed, car?.lap_progress])

    const handleCommand = useCallback((cmd) => {
        if (sendCommand && (car?.driver || selectedDriver)) {
            sendCommand(car?.driver || selectedDriver, cmd)
        }
    }, [sendCommand, car?.driver, selectedDriver])

    if (!selectedDriver) {
        return (
            <div className="telemetry-panel empty" style={{ height: '100%', minHeight: '600px' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '12px', opacity: 0.3 }}>📡</div>
                    <div style={{ fontSize: '0.8rem', letterSpacing: '2px', color: 'var(--text-tertiary)' }}>SELECT A DRIVER FOR TELEMETRY</div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-tertiary)', opacity: 0.5, marginTop: '8px' }}>Click a driver in the leaderboard</div>
                </div>
            </div>
        )
    }

    if (!car) return null

    // Derived data
    const tireWear = car.tire_wear || 0
    const tireCompound = car.tire_compound || 'SOFT'
    const tireAge = car.tire_age || 0
    const fuel = typeof car.fuel === 'number' ? car.fuel : 100
    const fuelPct = Math.min((fuel / 110) * 100, 100)
    const ersBattery = typeof car.ers_battery === 'number' ? car.ers_battery : 4
    const ersPct = (ersBattery / 4) * 100
    const drivingMode = car.driving_mode || 'BALANCED'

    // Strategic mock data
    const degRate = tireAge > 0 ? (tireWear / tireAge).toFixed(2) : '0.12'
    const estCliffLap = car.lap ? Math.round(car.lap + ((70 - tireWear) / parseFloat(degRate))) : '--'
    const undercutDelta = (driverAhead && driverAhead.interval !== null && driverAhead.interval !== undefined && driverAhead.interval < 3.0) ? `+${(Math.random() * 1.5 + 0.5).toFixed(1)}s` : '--'

    // ERS Tactical Logic
    const ersMode = drivingMode === 'PUSH' ? 'ATTACK' : (drivingMode === 'CONSERVE' ? 'HARVEST' : 'BALANCED')
    const ersLapsRemain = ersMode === 'ATTACK' ? Math.max(1, Math.round(ersPct / 30)) : '--'

    // Risk Meter -> (wear * 0.4) + (fuel * 0.4) + (ers * 0.2)
    const riskLevel = Math.round((tireWear * 0.4) + ((100 - fuelPct) * 0.4) + ((100 - ersPct) * 0.2))
    const riskColor = riskLevel > 70 ? '#ff3333' : riskLevel > 40 ? '#ffd600' : '#00e676'

    const tireColor = { SOFT: '#FF3333', MEDIUM: '#FFDD00', HARD: '#FFFFFF', INTERMEDIATE: '#00CC66', WET: '#0066FF' }[tireCompound] || '#FFF'

    const getWearColor = (wear) => {
        if (wear < 40) return '#00e676'
        if (wear < 70) return '#ffd600'
        return '#ff3333'
    }

    const rpmPct = ((simulatedTelemetry.rpm - 4000) / 8500) * 100

    return (
        <div className="telemetry-panel" style={{ height: 'calc(100vh - 220px)', padding: '20px', gap: '16px' }}>
            {/* === HEADER: Driver + Team + Commands === */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--glass-border)', paddingBottom: '14px' }}>
                <div>
                    <h2 style={{ fontSize: '2.5rem', fontWeight: 900, fontStyle: 'italic', letterSpacing: '-2px', color: 'rgba(255,255,255,0.9)', margin: 0, lineHeight: 1 }}>
                        {car.driver || selectedDriver}
                    </h2>
                    <span style={{ fontSize: '0.8rem', fontWeight: 700, letterSpacing: '3px', color: 'var(--red)', textTransform: 'uppercase' }}>
                        {car.team || 'TEAM'}
                    </span>
                </div>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <button className="btn btn-box" style={{ fontSize: '0.7rem', padding: '6px 12px' }} onClick={() => handleCommand('BOX_THIS_LAP')} title="Box Box">📦 BOX</button>
                    <button className="btn btn-push" style={{ fontSize: '0.7rem', padding: '6px 12px' }} onClick={() => handleCommand('PUSH')} title="Push Mode">🚀 PUSH</button>
                    <button className="btn btn-conserve" style={{ fontSize: '0.7rem', padding: '6px 12px' }} onClick={() => handleCommand('CONSERVE')} title="Conserve Mode">🍃 SAVE</button>
                </div>
            </div>

            {/* === HERO METRICS: Speed + Gear + RPM === */}
            <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '16px', alignItems: 'stretch' }}>
                {/* Gear box */}
                <div style={{ background: 'rgba(0,0,0,0.5)', borderRadius: '12px', padding: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--glass-border)' }}>
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '2px' }}>GEAR</span>
                    <span style={{ fontSize: '4rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--cyan)', lineHeight: 1 }}>{simulatedTelemetry.gear}</span>
                </div>

                {/* Speed + RPM */}
                <div style={{ background: 'rgba(0,0,0,0.5)', borderRadius: '12px', padding: '16px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', position: 'relative', overflow: 'hidden' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                                <span style={{
                                    fontSize: '3.5rem', fontWeight: 700, fontFamily: 'var(--font-mono)', lineHeight: 1,
                                    color: Math.round(car.speed || 0) > 280 ? 'var(--red)' : Math.round(car.speed || 0) > 180 ? 'var(--yellow)' : 'white',
                                    textShadow: Math.round(car.speed || 0) > 280 ? '0 0 10px rgba(255, 51, 51, 0.5)' : 'none',
                                    transition: 'color 0.2s ease, text-shadow 0.2s ease'
                                }}>
                                    {Math.round(car.speed || 0)}
                                </span>
                                <span style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', fontWeight: 700 }}>KM/H</span>
                            </div>
                            <div style={{ fontSize: '0.7rem', color: speedDelta > 0 ? 'var(--green)' : speedDelta < 0 ? 'var(--red)' : 'var(--text-tertiary)', fontWeight: 700, marginTop: '2px', display: 'flex', gap: '4px', alignItems: 'center' }}>
                                <span>{speedDelta > 0 ? '▲' : speedDelta < 0 ? '▼' : '-'}</span>
                                <span>{Math.abs(speedDelta)} km/h</span>
                            </div>
                        </div>
                        <div style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <div style={{ background: 'rgba(255,255,255,0.05)', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
                                <div style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', letterSpacing: '1px', marginBottom: '2px' }}>DELTA TO {driverAhead?.driver || 'LDR'}</div>
                                <div style={{ fontSize: '1.2rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: (driverAhead?.interval || car.gap_to_leader) ? 'var(--yellow)' : 'var(--green)' }}>
                                    {car.position === 1 ? 'P1' : `+${(driverAhead?.interval || car.gap_to_leader || 0).toFixed(2)}s`}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* RPM Bar */}
                    <div style={{ marginTop: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', letterSpacing: '1px' }}>RPM</span>
                            <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{Math.round(simulatedTelemetry.rpm)}</span>
                        </div>
                        <div className="rpm-bar-container" style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
                            <div className="rpm-bar-fill" style={{ height: '100%', width: `${rpmPct}%`, background: 'linear-gradient(90deg, #00e676, #ffd600, #ff3333)', borderRadius: '4px', transition: 'width 0.1s linear', boxShadow: rpmPct > 95 ? '0 0 12px rgba(255,51,51,0.6)' : 'none' }} />
                        </div>
                    </div>

                    {/* DRS/ERS Status */}
                    <div style={{ marginTop: '8px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <span style={{
                            fontSize: '0.65rem', fontWeight: 700, letterSpacing: '1px', padding: '3px 10px', borderRadius: '4px',
                            background: simulatedTelemetry.drs ? 'rgba(0,230,118,0.15)' : 'rgba(255,255,255,0.03)',
                            color: simulatedTelemetry.drs ? 'var(--green)' : 'var(--text-tertiary)',
                            border: `1px solid ${simulatedTelemetry.drs ? 'var(--green)' : 'transparent'}`
                        }}>
                            DRS {simulatedTelemetry.drs ? 'OPEN' : 'CLOSED'}
                        </span>
                        <span style={{
                            fontSize: '0.65rem', fontWeight: 700, letterSpacing: '1px', padding: '3px 10px', borderRadius: '4px',
                            background: car.ers_deployed ? 'rgba(0,229,255,0.15)' : 'rgba(255,255,255,0.03)',
                            color: car.ers_deployed ? 'var(--cyan)' : 'var(--text-tertiary)',
                            border: `1px solid ${car.ers_deployed ? 'var(--cyan)' : 'transparent'}`
                        }}>
                            ERS {car.ers_deployed ? 'DEPLOY' : 'CHARGE'}
                        </span>
                    </div>
                </div>
            </div>

            {/* === RPM LIVE GRAPH === */}
            <div className="hover-elevate" style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '10px', padding: '12px', border: '1px solid var(--glass-border)', transition: 'transform 0.2s, box-shadow 0.2s' }}>
                <div style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1.5px', marginBottom: '6px' }}>RPM TRACE</div>
                <div className="telemetry-line-container" style={{ width: '100%', height: '70px', position: 'relative' }}>
                    {rpmHistory.length > 1 ? (
                        <>
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={rpmHistory} margin={{ top: 2, right: 4, left: -20, bottom: 0 }}>
                                    <YAxis domain={[3000, 13000]} stroke="#333" fontSize={8} tickLine={false} axisLine={false} tickCount={3} tickFormatter={v => `${(v / 1000).toFixed(0)}k`} />
                                    <Line type="monotone" dataKey="rpm" stroke="var(--cyan)" strokeWidth={1.5} dot={false} isAnimationActive={false} className="telemetry-animated-line" />
                                </LineChart>
                            </ResponsiveContainer>
                            <div className="telemetry-graph-glow" style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none', background: 'linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.05), transparent)', animation: 'graphScan 3s linear infinite' }} />
                        </>
                    ) : (
                        <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.6rem', color: 'var(--text-tertiary)' }}>
                            Collecting data...
                        </div>
                    )}
                </div>
            </div>

            {/* === DATA GRID: Throttle/Brake | Tires | ERS/Fuel/Status === */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr 1fr', gap: '12px', flex: 1, minHeight: 0 }}>
                {/* INPUTS: Throttle + Brake bars */}
                <div className="hover-elevate" style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '10px', padding: '14px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', transition: 'transform 0.2s, box-shadow 0.2s' }}>
                    <h3 style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1.5px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '6px', marginBottom: '12px', marginTop: 0 }}>INPUTS</h3>
                    <div style={{ display: 'flex', gap: '20px', flex: 1, justifyContent: 'center', alignItems: 'stretch' }}>
                        {/* Throttle */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                            <div style={{ width: '24px', flex: 1, background: 'rgba(255,255,255,0.04)', borderRadius: '12px', position: 'relative', overflow: 'hidden', minHeight: '80px' }}>
                                <div style={{ position: 'absolute', bottom: 0, width: '100%', height: `${simulatedTelemetry.throttle}%`, background: 'linear-gradient(to top, #00c853, #00e676)', borderRadius: '12px', transition: 'height 0.1s linear', boxShadow: '0 0 8px rgba(0,230,118,0.3)' }} />
                            </div>
                            <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#00e676', marginTop: '6px', letterSpacing: '0.5px' }}>THR</span>
                            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{Math.round(simulatedTelemetry.throttle)}%</span>
                        </div>
                        {/* Brake */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1 }}>
                            <div style={{ width: '24px', flex: 1, background: 'rgba(255,255,255,0.04)', borderRadius: '12px', position: 'relative', overflow: 'hidden', minHeight: '80px' }}>
                                <div style={{ position: 'absolute', bottom: 0, width: '100%', height: `${simulatedTelemetry.brake}%`, background: 'linear-gradient(to top, #d50000, #ff5252)', borderRadius: '12px', transition: 'height 0.1s linear', boxShadow: '0 0 8px rgba(255,50,50,0.3)' }} />
                            </div>
                            <span style={{ fontSize: '0.6rem', fontWeight: 700, color: '#ff5252', marginTop: '6px', letterSpacing: '0.5px' }}>BRK</span>
                            <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{Math.round(simulatedTelemetry.brake)}%</span>
                        </div>
                    </div>
                </div>

                {/* TIRES */}
                <div className="hover-elevate" style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '10px', padding: '14px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', transition: 'transform 0.2s, box-shadow 0.2s' }}>
                    <h3 style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1.5px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '6px', marginBottom: '12px', marginTop: 0 }}>TYRE STRATEGY</h3>
                    <div style={{ flex: 1, display: 'flex', gap: '12px', alignItems: 'center' }}>
                        {/* Tire Image + Label */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                            <div style={{
                                width: '64px', height: '64px', borderRadius: '50%',
                                border: `3px solid ${tireColor}`, display: 'flex',
                                alignItems: 'center', justifyContent: 'center',
                                fontSize: '1.6rem', fontWeight: 700, color: '#fff',
                                backgroundColor: '#111', flexShrink: 0,
                                boxShadow: `0 0 15px ${tireColor}40`
                            }}>
                                {tireLetter}
                            </div>
                            <span style={{ fontSize: '0.65rem', fontWeight: 700, letterSpacing: '1px', color: tireColor }}>{tireCompound}</span>
                            <span style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>{tireAge} Laps</span>
                        </div>

                        {/* 4-corner layout */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gridTemplateRows: 'auto auto', gap: '6px', alignItems: 'center', justifyItems: 'center', width: '100%', maxWidth: '200px' }}>
                            <TireCorner label="FL" temp={simulatedTelemetry.tireTemps[0]} wear={tireWear} />
                            <div style={{ gridRow: '1 / 3', width: '32px', height: '60px', border: '2px solid rgba(255,255,255,0.15)', borderRadius: '8px' }} />
                            <TireCorner label="FR" temp={simulatedTelemetry.tireTemps[1]} wear={tireWear} />
                            <TireCorner label="RL" temp={simulatedTelemetry.tireTemps[2]} wear={Math.max(0, tireWear * 0.9)} />
                            <TireCorner label="RR" temp={simulatedTelemetry.tireTemps[3]} wear={Math.max(0, tireWear * 0.9)} />
                        </div>
                    </div>

                    {/* Overall wear bar */}
                    <div style={{ width: '100%', maxWidth: '200px', marginTop: '8px', alignSelf: 'center' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                            <span style={{ fontSize: '0.55rem', color: 'var(--text-tertiary)', letterSpacing: '1px' }}>WEAR</span>
                            <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: getWearColor(tireWear) }}>{tireWear.toFixed(0)}%</span>
                        </div>
                        <div style={{ height: '5px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginBottom: '8px' }}>
                            <div style={{ height: '100%', width: `${tireWear}%`, background: getWearColor(tireWear), borderRadius: '3px', transition: 'width 0.3s, background 0.3s' }} />
                        </div>
                        {/* Strategic Upgrade Info */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '6px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                                <span style={{ color: 'var(--text-tertiary)' }}>Deg Rate</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'white' }}>{degRate}%/L</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', textAlign: 'center' }}>
                                <span style={{ color: 'var(--text-tertiary)' }}>Est Cliff</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--yellow)' }}>L{estCliffLap}</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', textAlign: 'right' }}>
                                <span style={{ color: 'var(--text-tertiary)' }}>Undercut</span>
                                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: undercutDelta.startsWith('+') ? 'var(--green)' : 'var(--text-tertiary)' }}>{undercutDelta}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* SYSTEMS */}
                <div className="hover-elevate" style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '10px', padding: '14px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', transition: 'transform 0.2s, box-shadow 0.2s' }}>
                    <h3 style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1.5px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '6px', marginBottom: '12px', marginTop: 0 }}>SYSTEMS</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
                        {/* ERS Battery tactical */}
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1px' }}>ERS</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <span style={{ fontSize: '0.55rem', padding: '2px 4px', borderRadius: '3px', background: ersMode === 'ATTACK' ? 'rgba(255,51,51,0.2)' : ersMode === 'HARVEST' ? 'rgba(0,230,118,0.2)' : 'rgba(255,255,255,0.1)', color: ersMode === 'ATTACK' ? 'var(--red)' : ersMode === 'HARVEST' ? 'var(--green)' : 'var(--text-secondary)' }}>
                                        {ersMode}
                                    </span>
                                    <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--cyan)' }}>{Math.round(ersPct)}%</span>
                                </div>
                            </div>
                            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginBottom: '4px' }}>
                                <div style={{ height: '100%', width: `${ersPct}%`, background: 'var(--cyan)', borderRadius: '3px', transition: 'width 0.3s', boxShadow: '0 0 6px rgba(0,229,255,0.3)' }} />
                            </div>
                            <div style={{ fontSize: '0.55rem', color: 'var(--text-tertiary)', textAlign: 'right' }}>
                                Est. Deploy: {ersLapsRemain} laps
                            </div>
                        </div>

                        {/* Fuel */}
                        <StatusRow label="FUEL" value={`${fuel.toFixed(1)} kg`} color="var(--green)">
                            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden', marginTop: '3px' }}>
                                <div style={{ height: '100%', width: `${fuelPct}%`, background: fuel < 20 ? 'var(--red)' : 'var(--green)', borderRadius: '3px', transition: 'width 0.3s' }} />
                            </div>
                        </StatusRow>

                        {/* Divider */}
                        <div style={{ borderTop: '1px solid var(--glass-border)', margin: '2px 0' }} />

                        {/* Strategic Risk Meter */}
                        <div style={{ marginBottom: '4px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1px' }}>STRATEGIC RISK</span>
                                <span style={{ fontSize: '0.65rem', fontWeight: 700, color: riskColor }}>
                                    {riskLevel}% ({riskLevel > 70 ? 'HIGH' : riskLevel > 40 ? 'MED' : 'LOW'})
                                </span>
                            </div>
                            <div style={{ width: '100%', height: '4px', background: 'rgba(255,255,255,0.06)', borderRadius: '2px', overflow: 'hidden' }}>
                                <div style={{ height: '100%', width: `${Math.min(riskLevel, 100)}%`, background: riskColor, borderRadius: '2px', transition: 'width 0.3s, background 0.3s' }} />
                            </div>
                        </div>

                        {/* Status fields — label muted / value bright */}
                        <StatusField label="Status" value={car.status || 'RACING'} />
                        <StatusField label="Mode" value={drivingMode} valueColor={drivingMode === 'PUSH' ? 'var(--red)' : drivingMode === 'CONSERVE' ? 'var(--green)' : 'var(--text-primary)'} />
                        <StatusField label="Pit Stops" value={car.pit_stops || 0} />
                        <StatusField label="Position" value={`P${car.position}`} valueColor="var(--yellow)" />
                    </div>
                </div>
            </div>
        </div>
    )
}

// --- Sub-components ---

const TireCorner = ({ label, temp, wear }) => {
    const wearHue = Math.max(0, (1 - (wear || 0) / 100) * 120)
    const wearColor = `hsl(${wearHue}, 85%, 50%)`
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
            <div style={{
                width: '36px', height: '44px', border: `2px solid ${wearColor}`, borderRadius: '6px',
                background: `${wearColor}15`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '1px'
            }}>
                <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'white' }}>{Math.round(temp || 80)}°</span>
            </div>
            <span style={{ fontSize: '0.5rem', fontWeight: 600, color: 'var(--text-tertiary)' }}>{label}</span>
        </div>
    )
}

const StatusRow = ({ label, value, color, children }) => (
    <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '1px' }}>{label}</span>
            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color }}>{value}</span>
        </div>
        {children}
    </div>
)

const StatusField = ({ label, value, valueColor = 'var(--text-primary)' }) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '3px 0' }}>
        <span style={{ fontSize: '0.65rem', fontWeight: 500, color: 'var(--text-tertiary)' }}>{label}</span>
        <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: valueColor }}>{String(value)}</span>
    </div>
)

export default TelemetryPanel
