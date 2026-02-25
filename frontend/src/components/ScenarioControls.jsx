import React, { useState } from 'react'

const ScenarioControls = ({ onModifierChange, isLoading }) => {
    const [modifiers, setModifiers] = useState({
        aggression: 1.0,
        sc_prob: 1.0,
        tire_deg: 1.0,
        weather: 'DRY'
    });

    const inputStyle = {
        width: '100%',
        accentColor: '#00dc64',
        cursor: isLoading ? 'wait' : 'pointer',
        opacity: isLoading ? 0.5 : 1
    }

    // Debounce the API call so it feels live but doesn't spam
    React.useEffect(() => {
        const timer = setTimeout(() => {
            if (onModifierChange) {
                onModifierChange(modifiers)
            }
        }, 300); // 300ms debounce
        return () => clearTimeout(timer);
    }, [modifiers, onModifierChange]);

    const handleModifier = (key, value) => {
        setModifiers(prev => ({ ...prev, [key]: value }));
    }

    return (
        <div className="scenario-controls panel" style={{ display: 'flex', gap: '24px', alignItems: 'center', padding: '12px 20px', marginBottom: '16px', background: 'radial-gradient(circle at 10% 20%, rgba(40,40,40,0.8) 0%, rgba(20,20,20,0.8) 100%)', border: '1px solid #333' }}>
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: '120px' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.8rem', letterSpacing: '2px', textShadow: '0 0 5px rgba(255,255,255,0.2)' }}>SCENARIO</span>
                <span style={{ fontSize: '0.65rem', color: 'var(--red)', fontWeight: 700, letterSpacing: '1px' }}>INJECTOR</span>
            </div>

            <div style={{ flex: 1, display: 'flex', gap: '20px', alignItems: 'center' }}>
                {/* Weather Toggle */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                    <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px' }}>TRACK WEATHER</span>
                    <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', overflow: 'hidden', border: '1px solid #333' }}>
                        <button
                            disabled={isLoading}
                            style={{ flex: 1, padding: '4px 0', fontSize: '0.7rem', fontWeight: 700, background: modifiers.weather === 'DRY' ? 'rgba(255,200,0,0.2)' : 'transparent', color: modifiers.weather === 'DRY' ? '#ffc800' : '#888', border: 'none', cursor: isLoading ? 'wait' : 'pointer', transition: 'all 0.2s', opacity: isLoading ? 0.5 : 1 }}
                            onClick={() => handleModifier('weather', 'DRY')}
                        >
                            DRY
                        </button>
                        <button
                            disabled={isLoading}
                            style={{ flex: 1, padding: '4px 0', fontSize: '0.7rem', fontWeight: 700, background: modifiers.weather === 'RAIN' ? 'rgba(100,196,255,0.2)' : 'transparent', color: modifiers.weather === 'RAIN' ? '#64C4FF' : '#888', border: 'none', borderLeft: '1px solid #333', cursor: isLoading ? 'wait' : 'pointer', transition: 'all 0.2s', opacity: isLoading ? 0.5 : 1 }}
                            onClick={() => handleModifier('weather', 'RAIN')}
                        >
                            WET
                        </button>
                    </div>
                </div>

                {/* Aggression Slider */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px' }}>OVERTAKE AGGRESSION</span>
                        <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.aggression}x</span>
                    </div>
                    <input type="range" min="0.5" max="1.5" step="0.1" value={modifiers.aggression} onChange={(e) => handleModifier('aggression', parseFloat(e.target.value))} disabled={isLoading} style={inputStyle} />
                </div>

                {/* SC Probability Slider */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px' }}>SC PROBABILITY</span>
                        <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.sc_prob}x</span>
                    </div>
                    <input type="range" min="0.0" max="3.0" step="0.1" value={modifiers.sc_prob} onChange={(e) => handleModifier('sc_prob', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#ffc800' }} />
                </div>

                {/* Tire Deg Slider */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px' }}>TIRE DEG MULTIPLIER</span>
                        <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.tire_deg}x</span>
                    </div>
                    <input type="range" min="0.5" max="2.0" step="0.1" value={modifiers.tire_deg} onChange={(e) => handleModifier('tire_deg', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#ff4444' }} />
                </div>
            </div>
        </div>
    )
}

export default ScenarioControls
