import React from 'react'

const VolatilityIndex = ({ raceState }) => {
    // Determine chaos meter base on race condition
    const isVSC = raceState?.race_control === 'VSC'
    const isSC = raceState?.race_control === 'SC'
    const isRain = raceState?.track?.condition === 'WET'

    // Simulate an index (0 to 100)
    let indexValue = 15 // base stable
    if (isRain) indexValue += 40
    if (isVSC) indexValue += 30
    if (isSC) indexValue += 60

    // Cap at 95
    indexValue = Math.min(indexValue, 95)

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

    return (
        <div className="volatility-index chart-widget hover-elevate" style={{ minHeight: '140px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 className="panel-title" style={{ marginBottom: 0 }}>VOLATILITY INDEX</h2>
                <div style={{ padding: '2px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)' }}>CHAOS METER</div>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', marginBottom: '8px' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1, fontFamily: 'var(--font-mono)', color: statusColor, textShadow: `0 0 15px ${statusColor}66` }}>
                    {indexValue}
                </span>
                <span style={{ fontSize: '0.8rem', color: '#888', paddingBottom: '4px', letterSpacing: '1px' }}>/ 100</span>
            </div>

            {/* Meter Bar */}
            <div style={{ height: '8px', width: '100%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', marginBottom: '10px' }}>
                <div style={{
                    height: '100%',
                    width: `${indexValue}%`,
                    background: meterColor,
                    transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                    boxShadow: indexValue > 70 ? '0 0 10px rgba(255,68,68,0.6)' : 'none'
                }}></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.7rem', color: statusColor, fontWeight: 700, letterSpacing: '1px' }}>
                    {statusText}
                </span>
                <div style={{ display: 'flex', gap: '4px' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#00dc64', opacity: indexValue <= 40 ? 1 : 0.3 }}></div>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#ffc800', opacity: (indexValue > 40 && indexValue <= 70) ? 1 : 0.3 }}></div>
                    <div style={{ width: '8px', height: '8px', borderRadius: '2px', background: '#ff4444', opacity: indexValue > 70 ? 1 : 0.3 }}></div>
                </div>
            </div>
        </div>
    )
}

export default VolatilityIndex
