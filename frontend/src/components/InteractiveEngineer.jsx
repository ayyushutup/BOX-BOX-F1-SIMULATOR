import React from 'react';

const InteractiveEngineer = ({ selectedDriver, onCommand, disabled }) => {
    if (!selectedDriver) {
        return (
            <div className="panel overflow-hidden" style={{ minHeight: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: '#888', fontStyle: 'italic', fontSize: '0.9rem' }}>Select a driver to issue Engineer Commands</span>
            </div>
        );
    }

    return (
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#ffb703' }}>RACE ENGINEER: {selectedDriver}</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                <button
                    onClick={() => onCommand(selectedDriver, 'BOX')}
                    disabled={disabled}
                    className="btn"
                    style={{ backgroundColor: 'rgba(220, 38, 38, 0.2)', borderColor: '#dc2626', color: '#fca5a5', padding: '8px 4px', fontSize: '0.8rem', fontWeight: 'bold' }}
                >
                    BOX
                </button>
                <button
                    onClick={() => onCommand(selectedDriver, 'PUSH')}
                    disabled={disabled}
                    className="btn"
                    style={{ backgroundColor: 'rgba(202, 138, 4, 0.2)', borderColor: '#ca8a04', color: '#fef08a', padding: '8px 4px', fontSize: '0.8rem', fontWeight: 'bold' }}
                >
                    PUSH
                </button>
                <button
                    onClick={() => onCommand(selectedDriver, 'SAVE_TIRES')}
                    disabled={disabled}
                    className="btn"
                    style={{ backgroundColor: 'rgba(22, 163, 74, 0.2)', borderColor: '#16a34a', color: '#86efac', padding: '8px 4px', fontSize: '0.8rem', fontWeight: 'bold' }}
                >
                    SAVE TIRES
                </button>
            </div>
        </div>
    );
};

export default InteractiveEngineer;
