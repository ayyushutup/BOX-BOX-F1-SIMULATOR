import React, { useMemo } from 'react'

function TelemetryPanel({ selectedDriver, car, sendCommand }) {
    // Simulate Telemetry Data based on speed
    // HOOK MOVED TO TOP - MUST BE UNCONDITIONAL
    const simulatedTelemetry = useMemo(() => {
        if (!car) return { gear: 1, rpm: 4000, throttle: 0, brake: 0, drs: false }

        const speed = car.speed || 0
        const gear = Math.min(8, Math.max(1, Math.ceil(speed / 40)))

        // RPM Simulation: Curve based on speed within gear
        const gearBaseSpeed = (gear - 1) * 40
        const gearProgress = (speed - gearBaseSpeed) / 40
        const rpm = 4000 + (gearProgress * 8000) // 4k to 12k RPM

        return {
            gear,
            rpm: Math.min(12500, Math.max(4000, rpm)),
            throttle: speed > 0 ? 100 : 0,
            brake: 0,
            drs: car.drs_active
        }
    }, [car?.speed, car?.drs_active])

    // Command handler
    const handleCommand = (cmd) => {
        if (sendCommand && car?.driver) {
            sendCommand(car.driver, cmd)
        }
    }

    if (!selectedDriver) {
        return (
            <div className="telemetry-panel empty">
                <span>SELECT A DRIVER FOR TELEMETRY</span>
            </div>
        )
    }

    if (!car) return null

    return (
        <div className="telemetry-panel">
            <div className="telemetry-header">
                <span className="driver-name">{car.driver}</span>
                <span className="team-name">{car.team}</span>
                {car.active_command && (
                    <span className="active-command-badge">
                        {car.active_command === 'BOX_THIS_LAP' && '📦 BOX'}
                        {car.active_command === 'PUSH' && '🚀 PUSH'}
                        {car.active_command === 'CONSERVE' && '🍃 CONSERVE'}
                    </span>
                )}
            </div>

            <div className="telemetry-grid">
                {/* Speed & Gear */}
                <div className="telemetry-main">
                    <div className="gear-box">
                        <span className="label">GEAR</span>
                        <span className="value-gear">{simulatedTelemetry.gear}</span>
                    </div>
                    <div className="speed-box">
                        <span className="value-speed">{Math.round(car.speed)}</span>
                        <span className="unit">KPH</span>
                    </div>
                </div>

                {/* Bars */}
                <div className="telemetry-bars">
                    <div className="bar-row">
                        <span className="label">RPM</span>
                        <div className="bar-container">
                            <div
                                className="bar-fill rpm"
                                style={{ width: `${(simulatedTelemetry.rpm / 13000) * 100}%` }}
                            ></div>
                        </div>
                        <span className="value">{Math.round(simulatedTelemetry.rpm)}</span>
                    </div>
                    <div className="bar-row">
                        <span className="label">THR</span>
                        <div className="bar-container">
                            <div
                                className="bar-fill throttle"
                                style={{ width: `${simulatedTelemetry.throttle}%` }}
                            ></div>
                        </div>
                    </div>
                </div>

                {/* Status */}
                <div className="telemetry-status">
                    <div className={`status-item ${simulatedTelemetry.drs ? 'active' : ''}`}>
                        DRS
                    </div>
                    <div className={`status-item ${car.ers_deployed ? 'active' : ''}`}>
                        ERS
                    </div>
                    <div className="status-label">
                        BATT: {Math.round((car.ers_battery / 4) * 100)}%
                    </div>
                </div>
            </div>

            {/* TEAM PRINCIPAL COMMANDS */}
            <div className="command-buttons">
                <button
                    className="btn btn-box"
                    onClick={() => handleCommand('BOX_THIS_LAP')}
                    title="Order driver to pit at end of current lap"
                >
                    📦 BOX BOX
                </button>
                <button
                    className="btn btn-push"
                    onClick={() => handleCommand('PUSH')}
                    title="Push hard - faster but more tire/fuel wear"
                >
                    🚀 PUSH
                </button>
                <button
                    className="btn btn-conserve"
                    onClick={() => handleCommand('CONSERVE')}
                    title="Conserve tires and fuel"
                >
                    🍃 CONSERVE
                </button>
            </div>
        </div>
    )
}

export default TelemetryPanel
