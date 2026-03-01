import React, { useState, useRef, useEffect } from 'react'

// Tooltip descriptions — explains what each prediction control changes in the engine
const TIPS = {
    weather: 'Switches between dry and wet track conditions. Wet conditions increase aquaplaning risk, reduce grip, and dramatically change tire strategy. The ML model applies a rain modifier to all driver probabilities.',
    aggression: 'Scales how aggressively all drivers attack. Higher = more overtake attempts but higher crash risk. Feeds directly into the Monte Carlo noise model as a driver behavior multiplier.',
    sc_prob: 'Multiplier on base Safety Car deployment chance. At 2x+, expect multiple SC periods that compress the field and erase time gaps. Reshuffles strategy windows significantly.',
    tire_deg: 'Scales tire degradation rate across all compounds. At 1.5x+, expect 2-3 stop races with aggressive undercut opportunities. Below 0.7x, one-stop strategies dominate.',
    field_compression: 'Controls how close the field runs together. Higher values narrow pace gaps between drivers, making positions more volatile and overtakes more likely.',
    reliability: 'Scales mechanical reliability for all teams. Below 0.5x, expect frequent DNFs even for top teams. Above 1.5x, virtually no mechanical retirements.',
    qualifying_delta: 'Shifts the qualifying advantage for front-runners. Positive values boost P1-P5 win probability in logit space (P1 gets full effect, P20 gets 1/20th). Simulates qualifying pace gaps.',
    form_drift: 'When ON, doubles the weekend-to-weekend form variance (σ 0.12→0.24). Creates more upsets where normally dominant drivers underperform and midfielders outperform.',
    chaos_scaling: 'Controls the shape of chaos distribution. Linear = uniform noise. Exponential = noise grows with race distance. Clustered = 20% of simulations get a 2.5x noise burst, creating event clustering.',
};

// Tooltip component (same as ScenarioLab)
const Tooltip = ({ text, children, position = 'bottom' }) => {
    const [show, setShow] = useState(false);
    const timeoutRef = useRef(null);
    const handleEnter = () => { timeoutRef.current = setTimeout(() => setShow(true), 400); };
    const handleLeave = () => { clearTimeout(timeoutRef.current); setShow(false); };
    if (!text) return children;
    const posStyles = {
        top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' },
        bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' },
    };
    return (
        <div style={{ position: 'relative', display: 'inline-flex', width: '100%' }}
            onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
            {children}
            {show && (
                <div style={{
                    position: 'absolute', ...posStyles[position],
                    background: 'rgba(8, 8, 14, 0.97)', border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px', padding: '10px 14px', zIndex: 1000,
                    width: '240px', pointerEvents: 'none',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                    backdropFilter: 'blur(10px)',
                    animation: 'tooltipFadeIn 0.15s ease',
                }}>
                    <div style={{ fontSize: '0.65rem', color: '#ccc', lineHeight: 1.5, fontWeight: 400 }}>{text}</div>
                </div>
            )}
            <style>{`@keyframes tooltipFadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }`}</style>
        </div>
    );
};

const ScenarioControls = ({ onModifierChange, isLoading }) => {
    const [modifiers, setModifiers] = useState({
        aggression: 1.0,
        sc_prob: 1.0,
        tire_deg: 1.0,
        weather: 'DRY',
        field_compression: 1.0,
        reliability: 1.0,
        qualifying_delta: 0.0,
        form_drift: false,
        chaos_scaling: 'linear'
    });
    const [hasUserInteracted, setHasUserInteracted] = useState(false);

    const onModifierChangeRef = useRef(onModifierChange);
    useEffect(() => { onModifierChangeRef.current = onModifierChange; }, [onModifierChange]);

    const inputStyle = {
        width: '100%',
        accentColor: '#00dc64',
        cursor: isLoading ? 'wait' : 'pointer',
        opacity: isLoading ? 0.5 : 1
    }

    useEffect(() => {
        if (!hasUserInteracted) return;
        const timer = setTimeout(() => {
            if (onModifierChangeRef.current) {
                onModifierChangeRef.current(modifiers)
            }
        }, 400);
        return () => clearTimeout(timer);
    }, [modifiers, hasUserInteracted]);

    const handleModifier = (key, value) => {
        setHasUserInteracted(true);
        setModifiers(prev => ({ ...prev, [key]: value }));
    }

    return (
        <div className="scenario-controls panel" style={{ display: 'flex', gap: '16px', alignItems: 'center', padding: '12px 20px', marginBottom: '16px', background: 'radial-gradient(circle at 10% 20%, rgba(40,40,40,0.8) 0%, rgba(20,20,20,0.8) 100%)', border: '1px solid #333', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', minWidth: '120px' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.8rem', letterSpacing: '2px', textShadow: '0 0 5px rgba(255,255,255,0.2)' }}>SCENARIO</span>
                <span style={{ fontSize: '0.65rem', color: 'var(--red)', fontWeight: 700, letterSpacing: '1px' }}>INJECTOR</span>
            </div>

            <div style={{ flex: 1, display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
                {/* Weather Toggle */}
                <Tooltip text={TIPS.weather}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)', width: 'fit-content' }}>TRACK WEATHER</span>
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
                </Tooltip>

                {/* Aggression Slider */}
                <Tooltip text={TIPS.aggression}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>AGGRESSION</span>
                            <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.aggression}x</span>
                        </div>
                        <input type="range" min="0.5" max="1.5" step="0.1" value={modifiers.aggression} onChange={(e) => handleModifier('aggression', parseFloat(e.target.value))} disabled={isLoading} style={inputStyle} />
                    </div>
                </Tooltip>

                {/* SC Probability */}
                <Tooltip text={TIPS.sc_prob}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>SC PROB</span>
                            <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.sc_prob}x</span>
                        </div>
                        <input type="range" min="0.0" max="3.0" step="0.1" value={modifiers.sc_prob} onChange={(e) => handleModifier('sc_prob', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#ffc800' }} />
                    </div>
                </Tooltip>

                {/* Tire Deg */}
                <Tooltip text={TIPS.tire_deg}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>TIRE DEG</span>
                            <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.tire_deg}x</span>
                        </div>
                        <input type="range" min="0.5" max="2.0" step="0.1" value={modifiers.tire_deg} onChange={(e) => handleModifier('tire_deg', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#ff4444' }} />
                    </div>
                </Tooltip>

                {/* Field Compression */}
                <Tooltip text={TIPS.field_compression}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>FIELD COMP</span>
                            <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.field_compression}x</span>
                        </div>
                        <input type="range" min="0.5" max="2.0" step="0.1" value={modifiers.field_compression} onChange={(e) => handleModifier('field_compression', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#9B59B6' }} />
                    </div>
                </Tooltip>

                {/* Reliability */}
                <Tooltip text={TIPS.reliability}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>RELIABILITY</span>
                            <span style={{ fontSize: '0.65rem', color: '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.reliability}x</span>
                        </div>
                        <input type="range" min="0.0" max="2.0" step="0.1" value={modifiers.reliability} onChange={(e) => handleModifier('reliability', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#E74C3C' }} />
                    </div>
                </Tooltip>

                {/* P4: Qualifying Delta Override */}
                <Tooltip text={TIPS.qualifying_delta}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)' }}>QUALI Δ</span>
                            <span style={{ fontSize: '0.65rem', color: modifiers.qualifying_delta > 0 ? 'var(--green)' : modifiers.qualifying_delta < 0 ? 'var(--red)' : '#fff', fontFamily: 'var(--font-mono)' }}>{modifiers.qualifying_delta > 0 ? '+' : ''}{modifiers.qualifying_delta}s</span>
                        </div>
                        <input type="range" min="-2.0" max="2.0" step="0.1" value={modifiers.qualifying_delta} onChange={(e) => handleModifier('qualifying_delta', parseFloat(e.target.value))} disabled={isLoading} style={{ ...inputStyle, accentColor: '#3498DB' }} />
                    </div>
                </Tooltip>

                {/* P4: Form Drift Toggle */}
                <Tooltip text={TIPS.form_drift}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '90px' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)', width: 'fit-content' }}>FORM DRIFT</span>
                        <div style={{ display: 'flex', background: 'rgba(0,0,0,0.3)', borderRadius: '4px', overflow: 'hidden', border: '1px solid #333' }}>
                            <button
                                disabled={isLoading}
                                style={{ flex: 1, padding: '4px 0', fontSize: '0.7rem', fontWeight: 700, background: !modifiers.form_drift ? 'rgba(255,255,255,0.08)' : 'transparent', color: !modifiers.form_drift ? '#fff' : '#888', border: 'none', cursor: isLoading ? 'wait' : 'pointer', transition: 'all 0.2s', opacity: isLoading ? 0.5 : 1 }}
                                onClick={() => handleModifier('form_drift', false)}
                            >
                                OFF
                            </button>
                            <button
                                disabled={isLoading}
                                style={{ flex: 1, padding: '4px 0', fontSize: '0.7rem', fontWeight: 700, background: modifiers.form_drift ? 'rgba(0,220,100,0.2)' : 'transparent', color: modifiers.form_drift ? '#00dc64' : '#888', border: 'none', borderLeft: '1px solid #333', cursor: isLoading ? 'wait' : 'pointer', transition: 'all 0.2s', opacity: isLoading ? 0.5 : 1 }}
                                onClick={() => handleModifier('form_drift', true)}
                            >
                                ON
                            </button>
                        </div>
                    </div>
                </Tooltip>

                {/* P4: Chaos Scaling */}
                <Tooltip text={TIPS.chaos_scaling}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1, minWidth: '100px' }}>
                        <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '1px', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)', width: 'fit-content' }}>CHAOS MODE</span>
                        <select
                            value={modifiers.chaos_scaling}
                            onChange={(e) => handleModifier('chaos_scaling', e.target.value)}
                            disabled={isLoading}
                            style={{
                                background: 'rgba(0,0,0,0.5)', color: '#fff', border: '1px solid #333',
                                borderRadius: '4px', padding: '4px 6px', fontSize: '0.7rem',
                                fontWeight: 700, outline: 'none',
                                cursor: isLoading ? 'not-allowed' : 'pointer',
                                opacity: isLoading ? 0.5 : 1
                            }}
                        >
                            <option value="linear">Linear</option>
                            <option value="exponential">Exponential</option>
                            <option value="clustered">Clustered</option>
                        </select>
                    </div>
                </Tooltip>
            </div>
        </div>
    )
}

export default ScenarioControls
