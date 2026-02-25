import React from 'react'

const VolatilityIndex = ({ raceState, activeConfig }) => {
    // Determine chaos meter base on race condition and config
    const isVSC = raceState?.race_control === 'VSC'
    const isSC = raceState?.race_control === 'SC'

    // Evaluate active config for contributing factors
    const weatherProb = activeConfig?.weather?.timeline?.[0]?.rain_probability || (raceState?.track?.condition === 'WET' ? 1 : 0);
    const incidentFreq = activeConfig?.chaos?.incident_frequency || 1.0;
    const scProb = activeConfig?.chaos?.safety_car_probability || 1.0;

    // Average driver aggression from active config
    let avgAggression = 1.0;
    if (activeConfig?.drivers) {
        const drivers = Object.values(activeConfig.drivers);
        if (drivers.length > 0) {
            avgAggression = drivers.reduce((sum, d) => sum + (d.aggression || 1.0), 0) / drivers.length;
        }
    }

    // Simulate an index (0 to 100)
    let indexValue = 15 // base stable
    if (weatherProb > 0) indexValue += (weatherProb * 40);
    if (isVSC) indexValue += 15;
    if (isSC) indexValue += 30;

    // Add config multipliers
    indexValue += (incidentFreq - 1) * 20;
    indexValue += (scProb - 1) * 15;
    indexValue += (avgAggression - 1) * 25;

    // Cap at 95
    indexValue = Math.min(Math.max(indexValue, 5), 95);

    let statusText = 'STABLE'
    let statusColor = '#00dc64'
    let meterColor = 'linear-gradient(90deg, #00dc64, #00dc64)'

    if (indexValue > 40 && indexValue <= 70) {
        statusText = 'STRATEGIC'
        statusColor = '#ffc800'
        meterColor = 'linear-gradient(90deg, #00dc64, #ffc800)'
    } else if (indexValue > 70) {
        statusText = 'UNPREDICTABLE'
        statusColor = '#ff4444'
        meterColor = 'linear-gradient(90deg, #00dc64, #ffc800, #ff4444)'
    }

    // Determine highest contributors
    const contributors = [];
    if (weatherProb > 0.3) contributors.push('Weather');
    if (incidentFreq > 1.2 || scProb > 1.2) contributors.push('Chaos');
    if (avgAggression > 1.1) contributors.push('Driver');
    if (contributors.length === 0) contributors.push('Baseline Settings');

    return (
        <div className="volatility-index chart-widget hover-elevate" style={{ minHeight: '160px', borderTop: `2px solid ${statusColor}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 className="panel-title" style={{ marginBottom: 0, color: statusColor }}>VOLATILITY INDEX</h2>
                <div style={{ padding: '2px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>CHAOS METER</div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', marginBottom: '8px' }}>
                <span className="pulse-text" style={{
                    fontSize: '2.5rem',
                    fontWeight: 700,
                    lineHeight: 1,
                    fontFamily: 'var(--font-mono)',
                    color: statusColor,
                    textShadow: `0 0 ${indexValue > 70 ? '20px' : '10px'} ${statusColor}66`,
                    animation: indexValue > 70 ? 'pulse 1.5s infinite alternate' : 'none'
                }}>
                    {Math.round(indexValue)}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#888', paddingBottom: '4px', letterSpacing: '1px' }}>/ 100</span>
            </div>

            {/* Meter Bar */}
            <div style={{ height: '8px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', marginBottom: '10px' }}>
                <div style={{
                    height: '100%',
                    width: `${indexValue}%`,
                    background: meterColor,
                    transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: indexValue > 70 ? '0 0 10px rgba(255,68,68,0.6)' : 'none'
                }}></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ fontSize: '0.7rem', color: statusColor, fontWeight: 700, letterSpacing: '1px' }}>
                        {statusText}
                    </span>
                    <span style={{ fontSize: '0.65rem', color: '#aaa' }}>
                        Factors: {contributors.join(', ')}
                    </span>
                </div>
                <div style={{ display: 'flex', gap: '4px', marginTop: '2px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#00dc64', opacity: indexValue <= 40 ? 1 : 0.3 }}></div>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#ffc800', opacity: (indexValue > 40 && indexValue <= 70) ? 1 : 0.3 }}></div>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#ff4444', opacity: indexValue > 70 ? 1 : 0.3 }}></div>
                </div>
            </div>

            <style>{`
                @keyframes pulse {
                    0% { opacity: 0.8; transform: scale(1); }
                    100% { opacity: 1; transform: scale(1.05); }
                }
            `}</style>
        </div>
    )
}

export default VolatilityIndex

