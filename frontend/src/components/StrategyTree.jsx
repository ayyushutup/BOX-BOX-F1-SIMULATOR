import React from 'react'

const StrategyTree = ({ raceState }) => {
    // Generate static expected value matrix data
    const decisions = [
        { option: '1 STOP (SOFT -> HARD)', ev: 3.2, risk: 'LOW', confidence: 88, recommended: true },
        { option: '2 STOP (SOFT -> MED -> MED)', ev: 4.5, risk: 'MEDIUM', confidence: 65, recommended: false },
        { option: 'STAY OUT (LONG STINT)', ev: 6.8, risk: 'HIGH', confidence: 42, recommended: false },
    ];

    return (
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '220px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 className="panel-title" style={{ marginBottom: 0 }}>EXPECTED VALUE MATRIX</h2>
                <div className="text-xs text-gray-500 font-mono">STRATEGY OPTIONS</div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {decisions.map((decision, index) => (
                    <div
                        key={index}
                        style={{
                            background: decision.recommended ? 'rgba(0, 230, 118, 0.1)' : 'rgba(255, 255, 255, 0.03)',
                            border: decision.recommended ? '1px solid var(--green)' : '1px solid #333',
                            borderRadius: '4px',
                            padding: '12px',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '8px'
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: decision.recommended ? 'var(--green)' : '#fff' }}>
                                {decision.option}
                            </span>
                            {decision.recommended && <span style={{ fontSize: '0.6rem', padding: '2px 6px', background: 'var(--green)', color: '#000', borderRadius: '10px', fontWeight: 800 }}>OPTIMAL</span>}
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                                <span style={{ fontSize: '0.6rem', color: '#888' }}>EXPECTED FINISH</span>
                                <span style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>P{decision.ev.toFixed(1)}</span>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                <span style={{ fontSize: '0.6rem', color: '#888' }}>RISK / CONFIDENCE</span>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: decision.risk === 'HIGH' ? 'var(--red)' : decision.risk === 'MEDIUM' ? 'var(--orange)' : 'var(--green)' }}>
                                        {decision.risk}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', color: '#ccc', fontFamily: 'var(--font-mono)' }}>
                                        {decision.confidence}%
                                    </span>
                                </div>
                            </div>
                        </div>

                    </div>
                ))}
            </div>
        </div>
    )
}

export default StrategyTree;
