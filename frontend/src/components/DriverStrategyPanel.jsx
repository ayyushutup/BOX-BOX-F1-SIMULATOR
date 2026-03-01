import React from 'react'

const DriverStrategyPanel = ({ car, raceState, predictions }) => {
    if (!car) return null;

    // Derived strategic values
    const tirePhase = car.tire_wear > 75 ? 'CLIFF' : car.tire_wear > 40 ? 'DROP-OFF' : 'PEAK';
    const tirePhaseColor = tirePhase === 'CLIFF' ? 'var(--red)' : tirePhase === 'DROP-OFF' ? 'var(--orange)' : 'var(--green)';

    const undercutVuln = Math.min(100, Math.round(((car.tire_wear || 0) / 100) * 80 + 10));
    const vulnColor = undercutVuln > 70 ? 'var(--red)' : undercutVuln > 40 ? 'var(--orange)' : 'var(--green)';

    // Get interaction data from predictions
    const interactionMatrix = predictions?.interaction_matrix || {};
    const driverInteraction = interactionMatrix[car.driver] || null;

    // Get win probability for this driver
    const winProb = predictions?.mc_win_distribution?.[car.driver] || 0;
    const winPct = (winProb * 100).toFixed(1);

    // Get volatility band
    const band = predictions?.volatility_bands?.[car.driver] || {};
    const optPos = band.optimistic || car.position;
    const pesPos = band.pessimistic || car.position;

    return (
        <div className="panel" style={{ display: 'flex', gap: '24px', padding: '20px', backgroundColor: 'rgba(20, 20, 25, 0.95)', border: '1px solid #333', borderTop: `3px solid ${TEAM_COLORS[car.team] || '#555'}` }}>

            {/* Identity Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '150px' }}>
                <span style={{ fontSize: '0.7rem', color: '#888', letterSpacing: '2px' }}>STRATEGIC SNAPSHOT</span>
                <span style={{ fontSize: '2.5rem', fontWeight: 800, lineHeight: 1, color: TEAM_COLORS[car.team] || '#fff' }}>{car.driver}</span>
                <span style={{ fontSize: '0.8rem', color: '#bbb' }}>{car.team}</span>
                <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div>
                        <span style={{ fontSize: '0.6rem', color: '#888' }}>POS</span>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>P{car.position}</div>
                    </div>
                    <div>
                        <span style={{ fontSize: '0.6rem', color: '#888' }}>WIN%</span>
                        <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: winProb > 0.15 ? 'var(--green)' : '#ccc' }}>{winPct}%</div>
                    </div>
                </div>
                <div style={{ fontSize: '0.6rem', color: '#666', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
                    Band: P{optPos}–P{pesPos}
                </div>
            </div>

            <div style={{ width: '1px', background: '#333' }}></div>

            {/* Strategic State */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: '#ccc' }}>STRATEGIC STATE</span>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>TIRE PHASE</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tirePhaseColor }}>{tirePhase} ({Math.round(car.tire_wear || 0)}%)</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>UNDERCUT VULNERABILITY</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: vulnColor }}>{undercutVuln}%</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>OVERCUT WINDOW</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tirePhase === 'PEAK' ? 'var(--text-tertiary)' : 'var(--green)' }}>
                            {tirePhase === 'PEAK' ? 'CLOSED' : 'OPEN'}
                        </span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>TRAFFIC EXPOSURE RISK</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: car.position <= 3 ? 'var(--green)' : car.position <= 10 ? 'var(--orange)' : 'var(--red)' }}>
                            {car.position <= 3 ? 'LOW' : car.position <= 10 ? 'MEDIUM' : 'HIGH'}
                        </span>
                    </div>

                </div>
            </div>

            <div style={{ width: '1px', background: '#333' }}></div>

            {/* Interaction Matrix */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: '#ccc' }}>
                    INTERACTION MATRIX
                </span>

                {driverInteraction ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <div style={{ fontSize: '0.65rem', color: '#888' }}>
                            ACTIVE RIVALS ({driverInteraction.rivals.length})
                        </div>

                        {driverInteraction.rivals.map(rival => {
                            const rivalWin = predictions?.mc_win_distribution?.[rival] || 0;
                            const rivalBand = predictions?.volatility_bands?.[rival] || {};

                            return (
                                <div key={rival} style={{
                                    display: 'flex', alignItems: 'center', gap: '10px',
                                    padding: '6px 10px', borderRadius: '4px',
                                    background: 'rgba(255,68,68,0.06)',
                                    borderLeft: '3px solid rgba(255,68,68,0.4)'
                                }}>
                                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#ff6b6b', fontFamily: 'var(--font-mono)', width: '30px' }}>{rival}</span>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontSize: '0.6rem', color: '#888' }}>
                                            Win: {(rivalWin * 100).toFixed(1)}% | Band: P{rivalBand.optimistic || '?'}–P{rivalBand.pessimistic || '?'}
                                        </div>
                                    </div>
                                    <div style={{
                                        fontSize: '0.55rem', fontWeight: 700, color: '#ff4444',
                                        background: 'rgba(255,68,68,0.1)',
                                        padding: '2px 6px', borderRadius: '3px',
                                        fontFamily: 'var(--font-mono)'
                                    }}>
                                        {Math.round(driverInteraction.response_probability * 100)}% RESP
                                    </div>
                                </div>
                            );
                        })}

                        <div style={{ fontSize: '0.6rem', color: '#666', marginTop: '4px', fontStyle: 'italic' }}>
                            ⚔️ If {car.driver} surges, rivals boost with {Math.round(driverInteraction.response_probability * 100)}% probability
                        </div>
                    </div>
                ) : (
                    <div style={{ fontSize: '0.7rem', color: '#666', fontStyle: 'italic', padding: '8px 0' }}>
                        No active rivalry interactions for this driver
                    </div>
                )}
            </div>

        </div>
    )
}

const TEAM_COLORS = {
    'Red Bull Racing': '#3671C6',
    'Mercedes': '#6CD3BF',
    'Ferrari': '#F91536',
    'McLaren': '#F58020',
    'Aston Martin': '#358C75',
    'Alpine': '#2293D1',
    'Haas': '#B6BABD',
    'RB': '#6692FF',
    'Williams': '#64C4FF',
    'Kick Sauber': '#52E252',
};

export default DriverStrategyPanel;
