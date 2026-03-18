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
    const [isExpanded, setIsExpanded] = React.useState(false) // Collapse logic
    const [isMobile, setIsMobile] = React.useState(false)

    React.useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth <= 768);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    const sortedCars = [...cars].sort((a, b) => a.position - b.position)

    // Collapse logic: Show only 5 on mobile if not expanded
    const displayCars = isMobile && !isExpanded ? sortedCars.slice(0, 5) : sortedCars;

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

    const renderMobileCard = (car) => {
        const isLeader = car.position === 1
        const isSelected = selectedDriver === car.driver
        const teamColor = TEAM_COLORS[car.team] || '#333'

        const gapVal = gapMode === 'INTERVAL' ? car.interval : car.gap_to_leader
        const gapText = isLeader ? 'LEADER' : (gapVal !== null ? `+${gapVal.toFixed(1)}s` : '-')
        const paceBarWidth = gapVal && isFinite(gapVal) ? Math.max(10, 100 - (gapVal / maxGap) * 100) : 100;

        return (
            <div
                key={car.driver}
                className={`mobile-driver-card ${isSelected ? 'selected' : ''}`}
                onClick={() => onSelectDriver && onSelectDriver(car.driver)}
                style={{ borderLeft: `4px solid ${teamColor}` }}
            >
                <div className="card-top">
                    <div className="card-pos">{car.position}</div>
                    <div className="card-driver-info">
                        <span className="card-driver-name">{car.driver}</span>
                        <span className="card-team-name">{car.team}</span>
                    </div>
                    <div className="card-gap">{gapText}</div>
                </div>

                <div className="card-stats">
                    <div className="pace-visualization">
                        <div className="pace-label">Pace</div>
                        <div className="pace-track">
                            <div className="pace-fill" style={{ width: `${paceBarWidth}%`, background: teamColor }} />
                        </div>
                    </div>
                </div>

                {isSelected && (
                    <div className="card-selection-indicators">
                        <span className="tire-info">{car.tire_compound} - {car.tire_age}L</span>
                        {car.drs_active && <span className="drs-active">DRS</span>}
                    </div>
                )}
            </div>
        )
    }

    return (
        <div className={`tower ${isMobile ? 'mobile' : ''}`}>
            {!isMobile && (
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
                    >
                        {showExtras ? '◂' : '▸'}
                    </span>
                </div>
            )}

            <div className="tower-body" style={{ overflowY: 'auto', flex: 1 }}>
                {isMobile ? (
                    <div className="mobile-cards-container">
                        {displayCars.map(renderMobileCard)}
                        {sortedCars.length > 5 && !isExpanded && (
                            <button
                                className="show-more-btn"
                                onClick={() => setIsExpanded(true)}
                            >
                                SHOW FULL GRID ▼
                            </button>
                        )}
                        {isExpanded && (
                            <button
                                className="show-more-btn"
                                onClick={() => setIsExpanded(false)}
                            >
                                SHOW LESS ▲
                            </button>
                        )}
                    </div>
                ) : (
                    sortedCars.map((car) => {
                        const isLeader = car.position === 1
                        const isSelected = selectedDriver === car.driver
                        const isFastestLap = fastestLapHolder === car.driver
                        const isBattle = !isLeader && car.interval !== null && car.interval < 1.0

                        let gapVal = null
                        let gapText = '-'
                        let deltaAhead = null
                        let deltaBehind = null

                        const idx = sortedCars.findIndex(c => c.driver === car.driver)
                        if (idx > 0) deltaAhead = sortedCars[idx].interval
                        if (idx < sortedCars.length - 1) deltaBehind = sortedCars[idx + 1]?.interval

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
                        const tireWear = car.tire_wear || 0
                        const wearHue = Math.max(0, (1 - tireWear / 100) * 120)
                        const ersPercent = car.ers_battery !== undefined ? Math.round((car.ers_battery / 4) * 100) : null
                        const modeInfo = MODE_LABELS[car.driving_mode] || MODE_LABELS['BALANCED']

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
                                </div>

                                <div className="tower-tire">
                                    <div className="tire-badge-wrapper">
                                        <svg width="22" height="22" viewBox="0 0 22 22" style={{ position: 'absolute', left: '-3px', top: '-3px' }}>
                                            <circle cx="11" cy="11" r="9" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2" />
                                            <circle cx="11" cy="11" r="9" fill="none" stroke={`hsl(${wearHue}, 85%, 50%)`} strokeWidth="2"
                                                strokeDasharray={`${(1 - tireWear / 100) * 56.5} 56.5`}
                                                strokeLinecap="round" transform="rotate(-90 11 11)"
                                                style={{ transition: 'stroke-dasharray 0.3s, stroke 0.3s' }}
                                            />
                                        </svg>
                                        <div className="tire-badge" style={{ backgroundColor: tireColor, color: 'black', position: 'relative', zIndex: 1 }}>
                                            {tireLetter}
                                        </div>
                                    </div>
                                    <span style={{ fontSize: '0.7rem', opacity: 0.7, fontFamily: 'var(--font-mono)' }}>{car.tire_age}L</span>
                                </div>

                                {showExtras && (
                                    <>
                                        <div className="tower-extra" style={{ width: '45px' }}>
                                            <div className="mini-bar">
                                                <div className="mini-bar-fill" style={{ width: `${tireWear}%`, background: `hsl(${wearHue}, 85%, 45%)` }} />
                                            </div>
                                            <span className="mini-value">{tireWear.toFixed(0)}</span>
                                        </div>
                                        <div className="tower-extra" style={{ width: '40px' }}>
                                            <div className="mini-bar">
                                                <div className="mini-bar-fill" style={{ width: `${ersPercent || 0}%`, background: 'var(--cyan)' }} />
                                            </div>
                                            <span className="mini-value">{ersPercent ?? '-'}</span>
                                        </div>
                                        <div className="tower-extra" style={{ width: '38px' }}>
                                            <span className="mode-label" style={{ color: modeInfo.color, fontSize: '0.6rem', fontWeight: 700 }}>
                                                {modeInfo.text}
                                            </span>
                                        </div>
                                    </>
                                )}

                                <div className="tower-gap-col" style={{ width: '90px' }}>
                                    <div className="gap-text">{gapText}</div>
                                    {!isLeader && gapBarWidth > 0 && (
                                        <div className="gap-bar-track">
                                            <div className="gap-bar-fill" style={{ width: `${gapBarWidth}%`, backgroundColor: isBattle ? 'var(--yellow)' : 'rgba(255,255,255,0.12)' }} />
                                        </div>
                                    )}
                                </div>
                                <div style={{ width: '24px' }} />
                            </div>
                        )
                    })
                )}
            </div>

            <style>{`
                .mobile-cards-container {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    padding: 10px;
                }
                .mobile-driver-card {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 12px;
                    padding: 12px;
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                    transition: all 0.2s ease;
                }
                .mobile-driver-card.selected {
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255, 255, 255, 0.2);
                    transform: scale(1.02);
                }
                .card-top {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .card-pos {
                    font-size: 1.2rem;
                    font-weight: 800;
                    color: white;
                    width: 24px;
                }
                .card-driver-info {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                .card-driver-name {
                    font-size: 1.1rem;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }
                .card-team-name {
                    font-size: 0.75rem;
                    color: var(--text-tertiary);
                    text-transform: uppercase;
                }
                .card-gap {
                    font-family: var(--font-mono);
                    font-weight: 700;
                    font-size: 0.9rem;
                    color: var(--text-secondary);
                }
                .pace-visualization {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .pace-label {
                    font-size: 0.65rem;
                    color: var(--text-tertiary);
                    text-transform: uppercase;
                    width: 35px;
                }
                .pace-track {
                    flex: 1;
                    height: 4px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 2px;
                    overflow: hidden;
                }
                .pace-fill {
                    height: 100%;
                    border-radius: 2px;
                    transition: width 0.3s ease;
                }
                .show-more-btn {
                    background: rgba(225, 6, 0, 0.1);
                    border: 1px solid rgba(225, 6, 0, 0.2);
                    color: white;
                    padding: 12px;
                    border-radius: 10px;
                    font-weight: 700;
                    font-size: 0.8rem;
                    letter-spacing: 1px;
                    cursor: pointer;
                    margin-top: 10px;
                }
                .card-selection-indicators {
                    display: flex;
                    gap: 10px;
                    margin-top: 4px;
                }
                .tire-info {
                    font-size: 0.7rem;
                    background: rgba(255,255,255,0.05);
                    padding: 2px 8px;
                    border-radius: 4px;
                    color: var(--text-secondary);
                }
                .drs-active {
                    font-size: 0.7rem;
                    color: var(--green);
                    font-weight: 800;
                    animation: pulse 1s infinite;
                }
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.5; }
                    100% { opacity: 1; }
                }
            `}</style>
        </div>
    )
}

export default PositionTower
