import React from 'react'

// Team colors for F1 teams
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

function PositionTower({ cars, onSelectDriver, selectedDriver }) {
    const [gapMode, setGapMode] = React.useState('INTERVAL') // 'INTERVAL' or 'LEADER'

    // Sort by position (All cars)
    const sortedCars = [...cars]
        .sort((a, b) => a.position - b.position)

    // Tire colors
    const TIRE_COLORS = {
        'SOFT': '#FF3333',   // Red
        'MEDIUM': '#FFDD00', // Yellow
        'HARD': '#FFFFFF',   // White
        'INTERMEDIATE': '#00CC66', // Green
        'WET': '#0066FF'     // Blue
    }

    // Strategy icons
    const MODE_ICONS = {
        'PUSH': '🚀',
        'BALANCED': '',
        'CONSERVE': '🍃'
    }

    // Find fastest lap holder
    const bestLapTimes = sortedCars
        .filter(c => c.best_lap_time !== null && c.best_lap_time !== undefined)
        .map(c => ({ driver: c.driver, time: c.best_lap_time }))
    const fastestLapHolder = bestLapTimes.length > 0
        ? bestLapTimes.reduce((a, b) => a.time < b.time ? a : b).driver
        : null

    return (
        <div className="tower">
            <div className="tower-header">
                <span style={{ width: '40px', textAlign: 'center' }}>POS</span>
                <span style={{ flex: 1, paddingLeft: '8px' }}>DRIVER</span>
                <span style={{ width: '50px', textAlign: 'center' }}>TYRE</span>
                <span
                    style={{ width: '70px', textAlign: 'right', cursor: 'pointer', textDecoration: 'underline decoration-dotted' }}
                    onClick={() => setGapMode(gapMode === 'INTERVAL' ? 'LEADER' : 'INTERVAL')}
                >
                    {gapMode === 'INTERVAL' ? 'INT' : 'GAP'}
                </span>
                <span style={{ width: '70px', textAlign: 'right', paddingRight: '8px' }}>LAP</span>
            </div>
            <div className="tower-body" style={{ overflowY: 'auto', flex: 1 }}>
                {sortedCars.map((car) => {
                    const isLeader = car.position === 1
                    const isSelected = selectedDriver === car.driver
                    const isFastestLap = fastestLapHolder === car.driver

                    let gapText = '-'
                    if (gapMode === 'INTERVAL') {
                        gapText = isLeader ? '-' : (car.interval !== null ? `+${car.interval.toFixed(1)}` : '-')
                    } else {
                        gapText = isLeader ? '-' : (car.gap_to_leader !== null ? `+${car.gap_to_leader.toFixed(1)}` : '-')
                    }

                    // Battle mode: Gap < 1.0s and not leader
                    const isBattle = !isLeader && car.interval !== null && car.interval < 1.0

                    // Last lap time formatting
                    const lastLapText = car.last_lap_time ? car.last_lap_time.toFixed(1) : '-'

                    const tireColor = TIRE_COLORS[car.tire_compound] || '#FFF'
                    const tireLetter = car.tire_compound ? car.tire_compound[0] : 'U'

                    // Border color priority: selected > fastest lap > battle > default
                    let borderColor = 'transparent'
                    if (isSelected) borderColor = 'var(--red)'
                    else if (isFastestLap) borderColor = 'var(--purple)'
                    else if (isBattle) borderColor = 'var(--yellow)'

                    const modeIcon = MODE_ICONS[car.driving_mode] || ''

                    return (
                        <div
                            key={car.driver}
                            className={`tower-row ${isSelected ? 'selected' : ''}`}
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
                                {modeIcon && <span className="mode-icon">{modeIcon}</span>}
                                {car.active_command && (
                                    <span className="cmd-badge">
                                        {car.active_command === 'BOX_THIS_LAP' ? '📦' : ''}
                                    </span>
                                )}
                            </div>

                            {/* Tire Info */}
                            <div className="tower-tire">
                                <div className="tire-badge" style={{ backgroundColor: tireColor, color: 'black' }}>
                                    {tireLetter}
                                </div>
                                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>{car.tire_age}L</span>
                            </div>

                            {/* Gap/Interval */}
                            <div className="tower-interval" style={{ color: isBattle && gapMode === 'INTERVAL' ? 'var(--yellow)' : 'var(--text-secondary)', fontWeight: isBattle ? 700 : 400 }}>
                                {gapText}
                            </div>

                            {/* Last Lap */}
                            <div className="tower-interval" style={{ width: '70px', color: isFastestLap ? 'var(--purple)' : 'var(--text-tertiary)' }}>
                                {lastLapText}
                                {isFastestLap && <span style={{ marginLeft: '2px', fontSize: '0.6rem' }}>⚡</span>}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default PositionTower
