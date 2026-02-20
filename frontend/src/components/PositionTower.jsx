import React from 'react'

const TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF',
    'Ferrari': '#DC0000',
    'Mercedes': '#00D2BE',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'RB': '#2B4562',
    'Haas': '#B6BABD',
    'Sauber': '#52E252',
}

const TIRE_COLORS = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFDD00',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#00CC66',
    'WET': '#0066FF'
}

const MODE_LABELS = {
    'PUSH': { text: 'PUSH', color: 'var(--red)' },
    'BALANCED': { text: 'BAL', color: 'var(--text-tertiary)' },
    'CONSERVE': { text: 'SAVE', color: 'var(--green)' },
}

function PositionTower({ cars, onSelectDriver, selectedDriver }) {
    const [gapMode, setGapMode] = React.useState('INTERVAL')
    const [showExtras, setShowExtras] = React.useState(false)

    const sortedCars = [...cars].sort((a, b) => a.position - b.position)

    // Find fastest lap holder
    const bestLapTimes = sortedCars
        .filter(c => c.best_lap_time !== null && c.best_lap_time !== undefined)
        .map(c => ({ driver: c.driver, time: c.best_lap_time }))
    const fastestLapHolder = bestLapTimes.length > 0
        ? bestLapTimes.reduce((a, b) => a.time < b.time ? a : b).driver
        : null

    // Max gap for gap bar scaling
    const maxGap = React.useMemo(() => {
        const gaps = sortedCars
            .map(c => gapMode === 'INTERVAL' ? c.interval : c.gap_to_leader)
            .filter(g => g !== null && g !== undefined && isFinite(g))
        return Math.max(...gaps, 5)
    }, [sortedCars, gapMode])

    return (
        <div className="tower">
            <div className="tower-header">
                <span style={{ width: '40px', textAlign: 'center' }}>POS</span>
                <span style={{ flex: 1, paddingLeft: '8px' }}>DRIVER</span>
                <span style={{ width: '50px', textAlign: 'center' }}>TYRE</span>
                {showExtras && (
                    <>
                        <span style={{ width: '45px', textAlign: 'center', fontSize: '0.55rem' }}>WEAR</span>
                        <span style={{ width: '40px', textAlign: 'center', fontSize: '0.55rem' }}>ERS</span>
                        <span style={{ width: '38px', textAlign: 'center', fontSize: '0.55rem' }}>MODE</span>
                    </>
                )}
                <span
                    style={{ width: '90px', textAlign: 'right', cursor: 'pointer', textDecoration: 'underline decoration-dotted' }}
                    onClick={() => setGapMode(gapMode === 'INTERVAL' ? 'LEADER' : 'INTERVAL')}
                >
                    {gapMode === 'INTERVAL' ? 'INT' : 'GAP'}
                </span>
                <span
                    style={{ width: '24px', textAlign: 'center', cursor: 'pointer', opacity: 0.5, fontSize: '0.7rem' }}
                    onClick={() => setShowExtras(!showExtras)}
                    title="Toggle extra columns"
                >
                    {showExtras ? '◂' : '▸'}
                </span>
            </div>
            <div className="tower-body" style={{ overflowY: 'auto', flex: 1 }}>
                {sortedCars.map((car) => {
                    const isLeader = car.position === 1
                    const isSelected = selectedDriver === car.driver
                    const isFastestLap = fastestLapHolder === car.driver
                    const isBattle = !isLeader && car.interval !== null && car.interval < 1.0

                    let gapVal = null
                    let gapText = '-'
                    let deltaAhead = null
                    let deltaBehind = null

                    // Find car ahead and behind for tactical deltas
                    const idx = sortedCars.findIndex(c => c.driver === car.driver)
                    if (idx > 0) {
                        deltaAhead = sortedCars[idx].interval
                    }
                    if (idx < sortedCars.length - 1) {
                        deltaBehind = sortedCars[idx + 1]?.interval
                    }

                    if (gapMode === 'INTERVAL') {
                        gapVal = car.interval
                        gapText = isLeader ? 'LEADER' : (gapVal !== null ? `+${gapVal.toFixed(1)}` : '-')
                    } else {
                        gapVal = car.gap_to_leader
                        gapText = isLeader ? 'LEADER' : (gapVal !== null ? `+${gapVal.toFixed(1)}` : '-')
                    }
                    const gapBarWidth = gapVal && isFinite(gapVal) ? Math.min((gapVal / maxGap) * 100, 100) : 0

                    const tireColor = TIRE_COLORS[car.tire_compound] || '#FFF'
                    const tireLetter = car.tire_compound ? car.tire_compound[0] : 'U'

                    // Tire wear percentage for mini bar (0-100)
                    const tireWear = car.tire_wear || 0
                    const wearHue = Math.max(0, (1 - tireWear / 100) * 120)

                    // ERS percentage (0-4 MJ → 0-100%)
                    const ersPercent = car.ers_battery !== undefined ? Math.round((car.ers_battery / 4) * 100) : null

                    // Driving mode
                    const modeInfo = MODE_LABELS[car.driving_mode] || MODE_LABELS['BALANCED']

                    // Border color priority
                    let borderColor = 'transparent'
                    if (isSelected) borderColor = 'var(--red)'
                    else if (isFastestLap) borderColor = 'var(--purple)'
                    else if (isBattle) borderColor = 'var(--yellow)'

                    return (
                        <div
                            key={car.driver}
                            className={`tower-row ${isSelected ? 'selected' : ''} ${isBattle ? 'battle' : ''}`}
                            onClick={() => onSelectDriver && onSelectDriver(car.driver)}
                            style={{ cursor: 'pointer', borderLeft: `4px solid ${borderColor}` }}
                        >
                            <div
                                className="tower-position"
                                style={{ backgroundColor: isSelected ? 'var(--red)' : (TEAM_COLORS[car.team] || '#333') }}
                            >
                                {car.position}
                            </div>
                            <div className="tower-driver" style={{ color: isSelected ? 'white' : 'var(--text-primary)' }}>
                                {car.driver}
                                {car.in_pit_lane && <span className="pit-badge">PIT</span>}
                                {car.drs_active && <span className="drs-badge">DRS</span>}
                                {car.active_command && (
                                    <span className="cmd-badge">
                                        {car.active_command === 'BOX_THIS_LAP' ? '📦' : ''}
                                    </span>
                                )}
                            </div>

                            {/* Tire Info with age bar + health circle */}
                            <div className="tower-tire">
                                <div className="tire-badge-wrapper">
                                    {/* Tire health SVG circle */}
                                    <svg width="22" height="22" viewBox="0 0 22 22" style={{ position: 'absolute', left: '-3px', top: '-3px' }}>
                                        <circle cx="11" cy="11" r="9" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2" />
                                        <circle cx="11" cy="11" r="9" fill="none" stroke={`hsl(${wearHue}, 85%, 50%)`} strokeWidth="2"
                                            strokeDasharray={`${(1 - tireWear / 100) * 56.5} 56.5`}
                                            strokeLinecap="round"
                                            transform="rotate(-90 11 11)"
                                            style={{ transition: 'stroke-dasharray 0.3s, stroke 0.3s' }}
                                        />
                                    </svg>
                                    <div className="tire-badge" style={{ backgroundColor: tireColor, color: 'black', position: 'relative', zIndex: 1 }}>
                                        {tireLetter}
                                    </div>
                                    <div className="tire-age-bar">
                                        <div
                                            className="tire-age-fill"
                                            style={{
                                                width: `${Math.min(car.tire_age * 5, 100)}%`,
                                                backgroundColor: tireColor,
                                                opacity: 0.6,
                                            }}
                                        />
                                    </div>
                                </div>
                                <span style={{ fontSize: '0.7rem', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>{car.tire_age}L</span>
                            </div>

                            {/* Extra columns (toggled) */}
                            {showExtras && (
                                <>
                                    {/* Tire wear mini bar */}
                                    <div className="tower-extra" style={{ width: '45px' }}>
                                        <div className="mini-bar">
                                            <div
                                                className="mini-bar-fill"
                                                style={{
                                                    width: `${tireWear}%`,
                                                    background: `hsl(${wearHue}, 85%, 45%)`
                                                }}
                                            />
                                        </div>
                                        <span className="mini-value">{tireWear.toFixed(0)}</span>
                                    </div>

                                    {/* ERS */}
                                    <div className="tower-extra" style={{ width: '40px' }}>
                                        <div className="mini-bar">
                                            <div
                                                className="mini-bar-fill"
                                                style={{
                                                    width: `${ersPercent || 0}%`,
                                                    background: 'var(--cyan)'
                                                }}
                                            />
                                        </div>
                                        <span className="mini-value">{ersPercent ?? '-'}</span>
                                    </div>

                                    {/* Mode */}
                                    <div className="tower-extra" style={{ width: '38px' }}>
                                        <span className="mode-label" style={{ color: modeInfo.color, fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.5px' }}>
                                            {modeInfo.text}
                                        </span>
                                    </div>
                                </>
                            )}

                            {/* Gap/Interval with delta ahead/behind */}
                            <div className="tower-gap-col" style={{ width: '90px' }}>
                                <div className="gap-text" style={{
                                    color: isBattle && gapMode === 'INTERVAL' ? 'var(--yellow)' : 'var(--text-secondary)',
                                    fontWeight: isBattle ? 700 : 400
                                }}>
                                    {gapText}
                                </div>
                                {!isLeader && (
                                    <div style={{ display: 'flex', gap: '4px', marginTop: '1px' }}>
                                        {deltaAhead !== null && deltaAhead !== undefined && (
                                            <span style={{ fontSize: '0.55rem', fontFamily: 'var(--font-mono)', color: deltaAhead < 1.0 ? 'var(--yellow)' : 'var(--text-tertiary)' }}>
                                                ↑{deltaAhead.toFixed(1)}
                                            </span>
                                        )}
                                        {deltaBehind !== null && deltaBehind !== undefined && (
                                            <span style={{ fontSize: '0.55rem', fontFamily: 'var(--font-mono)', color: deltaBehind < 1.0 ? 'var(--cyan)' : 'var(--text-tertiary)' }}>
                                                ↓{deltaBehind.toFixed(1)}
                                            </span>
                                        )}
                                    </div>
                                )}
                                {!isLeader && gapBarWidth > 0 && (
                                    <div className="gap-bar-track">
                                        <div
                                            className="gap-bar-fill"
                                            style={{
                                                width: `${gapBarWidth}%`,
                                                backgroundColor: isBattle ? 'var(--yellow)' : 'rgba(255,255,255,0.12)'
                                            }}
                                        />
                                    </div>
                                )}
                            </div>

                            {/* Toggle spacer */}
                            <div style={{ width: '24px' }} />
                        </div>
                    )
                })}
            </div>

            <style>{`
                .tower-row.battle {
                    animation: battleFlash 2s ease-in-out infinite;
                }
                @keyframes battleFlash {
                    0%, 100% { background: transparent; }
                    50% { background: rgba(255, 214, 0, 0.04); }
                }
                .tire-badge-wrapper {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 2px;
                    position: relative;
                }
                .tire-age-bar {
                    width: 16px;
                    height: 2px;
                    background: rgba(255,255,255,0.06);
                    border-radius: 1px;
                    overflow: hidden;
                }
                .tire-age-fill {
                    height: 100%;
                    border-radius: 1px;
                    transition: width 0.3s;
                }
                .tower-extra {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 3px;
                    padding: 0 2px;
                }
                .mini-bar {
                    width: 20px;
                    height: 4px;
                    background: rgba(255,255,255,0.06);
                    border-radius: 2px;
                    overflow: hidden;
                }
                .mini-bar-fill {
                    height: 100%;
                    border-radius: 2px;
                    transition: width 0.3s ease;
                }
                .mini-value {
                    font-size: 0.6rem;
                    font-family: var(--font-mono);
                    color: var(--text-tertiary);
                    font-variant-numeric: tabular-nums;
                }
                .mode-label {
                    font-family: var(--font-mono);
                }
                .tower-gap-col {
                    display: flex;
                    flex-direction: column;
                    align-items: flex-end;
                    justify-content: center;
                    padding-right: 4px;
                }
                .gap-text {
                    font-size: 0.8rem;
                    font-family: var(--font-mono);
                    font-variant-numeric: tabular-nums;
                    line-height: 1.2;
                }
                .gap-bar-track {
                    width: 100%;
                    height: 2px;
                    background: rgba(255,255,255,0.03);
                    border-radius: 1px;
                    overflow: hidden;
                    margin-top: 2px;
                }
                .gap-bar-fill {
                    height: 100%;
                    border-radius: 1px;
                    transition: width 0.3s ease;
                }
            `}</style>
        </div>
    )
}

export default PositionTower
