import React from 'react'

const DriverStrategyPanel = ({ car, raceState }) => {
    if (!car) return null;

    // Derived strategic values for demonstration
    const tirePhase = car.tire_wear > 75 ? 'CLIFF' : car.tire_wear > 40 ? 'DROP-OFF' : 'PEAK';
    const tirePhaseColor = tirePhase === 'CLIFF' ? 'var(--red)' : tirePhase === 'DROP-OFF' ? 'var(--orange)' : 'var(--green)';

    const undercutVuln = Math.min(100, Math.round(((car.tire_wear || 0) / 100) * 80 + 10)); // proxy logic
    const vulnColor = undercutVuln > 70 ? 'var(--red)' : undercutVuln > 40 ? 'var(--orange)' : 'var(--green)';

    return (
        <div className="panel" style={{ display: 'flex', gap: '24px', padding: '20px', backgroundColor: 'rgba(20, 20, 25, 0.95)', border: '1px solid #333', borderTop: `3px solid ${TEAM_COLORS[car.team] || '#555'}` }}>

            {/* Identity Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '150px' }}>
                <span style={{ fontSize: '0.7rem', color: '#888', letterSpacing: '2px' }}>STRATEGIC SNAPSHOT</span>
                <span style={{ fontSize: '2.5rem', fontWeight: 800, lineHeight: 1, color: TEAM_COLORS[car.team] || '#fff' }}>{car.driver}</span>
                <span style={{ fontSize: '0.8rem', color: '#bbb' }}>{car.team}</span>
                <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.7rem', color: '#888' }}>POS</span>
                    <span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>P{car.position}</span>
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
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--orange)' }}>MEDIUM</span>
                    </div>

                </div>
            </div>

            <div style={{ width: '1px', background: '#333' }}></div>

            {/* Scenario Stress Response */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px', color: '#ccc' }}>SCENARIO STRESS RESPONSE</span>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>WET MULTIPLIER</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>1.04x</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>TIRE MGMT COEFF</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--green)' }}>0.92</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>PRESSURE STABILITY</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700 }}>HIGH</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '0.7rem', color: '#888' }}>SC RESTART GAIN</span>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--green)' }}>+0.12s</span>
                    </div>

                </div>
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
