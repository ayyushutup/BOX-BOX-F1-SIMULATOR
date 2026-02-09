import React from 'react'
import { useState } from 'react'

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
    const STRATEGY_ICONS = {
        'PUSH': '🚀',
        'BALANCED': '⚖️',
        'CONSERVE': '🍃'
    }

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
                {sortedCars.map((car, index) => {
                    const isLeader = car.position === 1
                    const isSelected = selectedDriver === car.driver

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

                    return (
                        <div
                            key={car.driver}
                            className={`tower-row ${isSelected ? 'selected' : ''}`}
                            onClick={() => onSelectDriver && onSelectDriver(car.driver)}
                            style={{ cursor: 'pointer', borderLeft: isSelected ? '4px solid var(--red)' : (isBattle ? '4px solid var(--yellow)' : '4px solid transparent') }}
                        >
                            <div
                                className="tower-position"
                                style={{ backgroundColor: isSelected ? 'var(--red)' : (TEAM_COLORS[car.team] || '#333') }}
                            >
                                {car.position}
                            </div>
                            <div className="tower-driver" style={{ color: isSelected ? 'white' : 'var(--text-main)' }}>
                                {car.driver}
                                {car.in_pit_lane && <span className="pit-badge">PIT</span>}
                            </div>

                            {/* Tire Info */}
                            <div className="tower-tire">
                                <div className="tire-badge" style={{ backgroundColor: tireColor, color: 'black' }}>
                                    {tireLetter}
                                </div>
                                <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>{car.tire_age}L</span>
                            </div>

                            {/* Gap/Interval */}
                            <div className="tower-interval" style={{ color: isBattle && gapMode === 'INTERVAL' ? 'var(--yellow)' : 'var(--text-main)', fontWeight: isBattle ? 700 : 400 }}>
                                {gapText}
                            </div>

                            {/* Last Lap */}
                            <div className="tower-interval" style={{ width: '70px', color: 'var(--text-dim)' }}>
                                {lastLapText}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default PositionTower
