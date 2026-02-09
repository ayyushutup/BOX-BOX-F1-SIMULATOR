import React from 'react'

function RaceControlStatus({ raceState }) {
    if (!raceState) return null

    const { safety_car_active, vsc_active, red_flag_active } = raceState

    let status = 'GREEN'
    let color = 'var(--green)'
    let message = 'TRACK CLEAR'
    let subtext = 'RACING'

    if (red_flag_active) {
        status = 'RED FLAG'
        color = 'var(--red)'
        message = 'SESSION SUSPENDED'
        subtext = 'RETURN TO PIT LANE'
    } else if (safety_car_active) {
        status = 'SAFETY CAR'
        color = 'var(--yellow)'
        message = 'SAFETY CAR DEPLOYED'
        subtext = 'NO OVERTAKING • REDUCED SPEED'
    } else if (vsc_active) {
        status = 'VSC'
        color = 'var(--yellow)'
        message = 'VIRTUAL SAFETY CAR'
        subtext = 'REDUCED SPEED • MAINTAIN DELTA'
    }

    return (
        <div className="race-status-container" style={{ borderLeft: `4px solid ${color}` }}>
            <div className="status-badge" style={{ backgroundColor: color }}>
                {status}
            </div>
            <div className="status-info">
                <div className="status-message" style={{ color: color }}>{message}</div>
                <div className="status-subtext">{subtext}</div>
            </div>
        </div>
    )
}

export default RaceControlStatus
