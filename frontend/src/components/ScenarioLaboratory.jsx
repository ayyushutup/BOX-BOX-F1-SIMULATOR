import React, { useState, useMemo, useRef } from 'react';

const CATEGORIES = [
    { id: 'RACE_STRUCTURE', label: 'Race Structure', desc: 'Track, laps, grid order & session config', icon: '🏁', color: '#3498DB' },
    { id: 'WEATHER', label: 'Weather Timeline', desc: 'Rain probability, temperature & conditions', icon: '🌦️', color: '#64C4FF' },
    { id: 'TEAMS', label: 'Team Ratings', desc: 'Engine power, aero, pit speed & reliability', icon: '⚙️', color: '#6CD3BF' },
    { id: 'ENGINEERING', label: 'Car Setup', desc: 'Downforce, drag & tire degradation tuning', icon: '🏎️', color: '#2ECC71' },
    { id: 'DRIVERS', label: 'Driver Persona', desc: 'Aggression, risk tolerance & tire management', icon: '🧠', color: '#E056A0' },
    { id: 'CHAOS', label: 'Chaos Engine', desc: 'Incident frequency, SC probability & randomness', icon: '🎲', color: '#E74C3C' }
];

const PRESETS = [
    { id: 'monaco_chaos', label: '🇲🇨 Monaco Chaos', config: { race_structure: { track_id: 'monaco', total_laps: 78 }, chaos: { incident_frequency: 2.5, safety_car_probability: 2.5, mechanical_randomness: 2.0, ai_irrationality: 1.5 }, weather: { timeline: [{ start_lap: 0, rain_probability: 0.0, temperature: 22.0 }] } } },
    { id: 'wet_race', label: '🌧️ Wet Race', config: { weather: { timeline: [{ start_lap: 0, rain_probability: 0.9, temperature: 16.0 }] }, chaos: { incident_frequency: 1.8, safety_car_probability: 2.0, mechanical_randomness: 1.5, ai_irrationality: 1.3 } } },
    { id: 'high_rel', label: '🟢 High Reliability', config: { chaos: { incident_frequency: 0.3, safety_car_probability: 0.3, mechanical_randomness: 0.2, ai_irrationality: 0.5 } } },
    { id: 'undercut', label: '🔧 Undercut Heavy', config: { engineering: { tire_deg_multiplier: 1.4, downforce_level: 0.9 }, chaos: { incident_frequency: 0.5, safety_car_probability: 0.5, mechanical_randomness: 0.5, ai_irrationality: 0.8 } } },
    { id: 'dominant', label: '👑 Dominant Leader', config: { chaos: { incident_frequency: 0.3, safety_car_probability: 0.2, mechanical_randomness: 0.3, ai_irrationality: 0.3 }, engineering: { tire_deg_multiplier: 0.8 } } },
];

const TIRE_COLORS = { SOFT: '#ff3333', MEDIUM: '#ffc800', HARD: '#ffffff', INTERMEDIATE: '#44cc44', WET: '#4488ff' };
const TEAM_COLORS = {
    'Red Bull Racing': '#3671C6', 'Mercedes': '#6CD3BF', 'Ferrari': '#F91536',
    'McLaren': '#F58020', 'Aston Martin': '#358C75', 'Alpine': '#2293D1',
    'Haas': '#B6BABD', 'Racing Bulls': '#6692FF', 'Williams': '#64C4FF',
    'Sauber': '#52E252', 'Kick Sauber': '#52E252',
};

// Impact levels for sliders
const IMPACT = {
    incident_frequency: 3, safety_car_probability: 3, mechanical_randomness: 2, ai_irrationality: 2,
    downforce_level: 2, drag_coefficient: 1, tire_deg_multiplier: 3,
    engine_power: 3, aero_efficiency: 2, pit_stop_speed: 2, reliability: 3,
    aggression: 3, risk_tolerance: 2, overtake_confidence: 2, defensive_skill: 1, tire_preservation: 2,
};

// Tooltip descriptions — explains what each control changes in the simulation engine
const TOOLTIPS = {
    // Chaos sliders
    incident_frequency: 'Scales the probability of on-track incidents per simulation tick. Higher values create more DNFs, collisions, and debris. Directly feeds the Monte Carlo stochastic layer.',
    safety_car_probability: 'Multiplier on the base Safety Car deployment chance. Higher values compress the field more often, erasing gaps and reshuffling strategy windows.',
    mechanical_randomness: 'Controls random mechanical failures (engine, gearbox, hydraulics). At 2x+, even top teams face significant retirement risk.',
    ai_irrationality: 'How unpredictably drivers behave — late braking, risky overtakes, defensive errors. Higher values increase the noise in driver decision-making.',
    // Engineering sliders
    downforce_level: 'Adjusts overall downforce. Higher = more grip in corners but more drag on straights. Affects overtaking difficulty and tire wear patterns.',
    drag_coefficient: 'Scales aerodynamic drag. Lower values favor top speed; higher values hurt straight-line performance but can improve braking stability.',
    tire_deg_multiplier: 'Scales tire degradation rate. At 1.4x+, pit strategy becomes critical — expect 2-3 stop races. Below 0.8x, one-stop strategies dominate.',
    // Team sliders
    engine_power: 'Scales the team\'s power unit output. Directly affects top speed and acceleration. A 10% boost ≈ 0.3s per lap advantage.',
    aero_efficiency: 'Team\'s aerodynamic package quality. Affects cornering speed and overall lap time. Higher = faster through technical sections.',
    pit_stop_speed: 'Team\'s pit crew efficiency. At 1.5x, pit stops are ~1.5s faster than baseline. Critical in undercut/overcut calculations.',
    reliability: 'Team\'s mechanical reliability rating. Below 0.7x, expect frequent retirements. Above 1.2x, virtually bulletproof.',
    // Driver sliders
    aggression: 'How aggressively the driver attacks. High aggression = more overtakes attempted but higher crash risk. Feeds directly into the Monte Carlo noise model.',
    risk_tolerance: 'Willingness to take risks in wheel-to-wheel combat. Higher values increase both overtake success rate AND incident probability.',
    overtake_confidence: 'Driver\'s ability to execute overtakes cleanly. High values = more successful passes on track. Low = tendency to get stuck in traffic.',
    defensive_skill: 'Ability to hold position under pressure. High values make the driver harder to pass. Affects how often rivals can counter-boost.',
    tire_preservation: 'How well the driver manages tire life. High values extend stint length, enabling later pit stops and strategic flexibility.',
    // Weather
    rain_start: 'The lap at which rain begins. Earlier rain = more disruption to strategy. If set beyond total laps, the race stays dry.',
    rain_probability: 'Chance of rain occurring. At 50%+, the simulation forces wet-weather adjustments. At 90%+, expect full wet conditions with aquaplaning risk.',
    temperature: 'Track surface temperature. Higher temps increase tire degradation. Below 15°C, tire warm-up becomes a factor (especially for hard compounds).',
    // Race structure
    track_selection: 'Choose the circuit. Each track has unique characteristics: abrasion level, downforce requirements, overtaking difficulty, and historical SC probability.',
    total_laps: 'Race distance in laps. Longer races emphasize strategy and reliability. Shorter races favor raw pace and grid position.',
    safety_car_toggle: 'When disabled, no Safety Cars deploy regardless of incidents. This removes a major source of variance from the simulation.',
    drs_toggle: 'DRS (Drag Reduction System) enables a speed boost in designated overtaking zones. Disabling it makes position changes much harder.',
    grid_position: 'Grid position is one of the 16 features in the ML model. Moving a driver forward significantly boosts their win probability — P1 starters win ~40% of races historically.',
    tire_compound: 'Starting tire compound affects grip, degradation rate, and first pit stop window. Soft = fast but short-lived, Hard = slow but durable.',
    // Presets
    'monaco_chaos': 'Sets Monaco circuit with max chaos: 2.5x incidents, 2.5x SC probability. Monaco\'s narrow streets amplify every disruption.',
    'wet_race': 'Simulates a full wet race: 90% rain probability, cold track (16°C), elevated chaos. Favors wet-weather specialists.',
    'high_rel': 'Clean race simulation: minimal incidents, low SC risk. Pure pace-based outcome — the fastest car and best strategy win.',
    'undercut': 'High tire degradation (1.4x) with low chaos. Creates a strategy-heavy race where pit stop timing determines the winner.',
    'dominant': 'Minimal variance scenario. Low chaos + low tire deg = the strongest car on the grid should dominate unchallenged.',
    // Buttons
    reset_section: 'Reset all parameters in this section back to their default baseline values.',
    reset_all: 'Reset the entire scenario configuration to factory defaults — grid order, chaos, weather, engineering, everything.',
    launch: 'Compile the current parameters and run the full prediction pipeline: LightGBM model → Bayesian logit composition → Monte Carlo simulation (5000 runs) → Commentary engine.',
    add_driver: 'Add a driver back to the starting grid. Their position will be at the rear of the field.',
    remove_driver: 'Remove this driver from the simulation entirely. They will not appear in predictions.',
    move_up: 'Move this driver one position forward on the grid. Grid position directly affects win probability in the ML model.',
    move_down: 'Move this driver one position back on the grid. Grid position directly affects win probability in the ML model.',
};

// Tooltip component
const Tooltip = ({ text, children, position = 'top' }) => {
    const [show, setShow] = useState(false);
    const timeoutRef = useRef(null);

    const handleEnter = () => {
        timeoutRef.current = setTimeout(() => setShow(true), 400);
    };
    const handleLeave = () => {
        clearTimeout(timeoutRef.current);
        setShow(false);
    };

    if (!text) return children;

    const posStyles = {
        top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: '8px' },
        bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: '8px' },
        left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: '8px' },
        right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: '8px' },
    };

    return (
        <div style={{ position: 'relative', display: 'inline-flex' }}
            onMouseEnter={handleEnter} onMouseLeave={handleLeave}>
            {children}
            {show && (
                <div style={{
                    position: 'absolute', ...posStyles[position],
                    background: 'rgba(8, 8, 14, 0.97)', border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px', padding: '10px 14px', zIndex: 1000,
                    width: '260px', pointerEvents: 'none',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.6)',
                    backdropFilter: 'blur(10px)',
                    animation: 'tooltipFadeIn 0.15s ease',
                }}>
                    <div style={{ fontSize: '0.68rem', color: '#ccc', lineHeight: 1.5, fontWeight: 400 }}>{text}</div>
                </div>
            )}
        </div>
    );
};

const defaultGrid = [
    { driver: "VER", team: "Red Bull Racing", position: 1, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "NOR", team: "McLaren", position: 2, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "LEC", team: "Ferrari", position: 3, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "HAM", team: "Ferrari", position: 4, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "RUS", team: "Mercedes", position: 5, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "PIA", team: "McLaren", position: 6, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "SAI", team: "Williams", position: 7, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "ALO", team: "Aston Martin", position: 8, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "GAS", team: "Alpine", position: 9, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "LAW", team: "Red Bull Racing", position: 10, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "ALB", team: "Williams", position: 11, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "TSU", team: "Racing Bulls", position: 12, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "HUL", team: "Sauber", position: 13, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "OCO", team: "Haas", position: 14, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "STR", team: "Aston Martin", position: 15, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "ANT", team: "Mercedes", position: 16, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "BEA", team: "Haas", position: 17, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "DOO", team: "Alpine", position: 18, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "HAD", team: "Racing Bulls", position: 19, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "BOR", team: "Sauber", position: 20, tire_compound: "MEDIUM", fuel_kg: 100 },
];

const defaultConfig = {
    race_structure: { track_id: "monaco", total_laps: 50, starting_lap: 0, drs_enabled: true, sc_enabled: true, pit_lane_time_delta: 20.0, grid: [...defaultGrid] },
    weather: { timeline: [{ start_lap: 0, rain_probability: 0.0, temperature: 25.0 }] },
    teams: {},
    engineering: { downforce_level: 1.0, drag_coefficient: 1.0, tire_deg_multiplier: 1.0 },
    drivers: {},
    chaos: { mechanical_randomness: 1.0, incident_frequency: 1.0, safety_car_probability: 1.0, ai_irrationality: 1.0 },
    seed: 42
};

// --- Small reusable components ---

const ImpactDots = ({ level, color }) => (
    <span style={{ fontSize: '0.6rem', color, fontFamily: 'var(--font-mono)', letterSpacing: '1px', opacity: 0.8 }}>
        {Array.from({ length: 3 }, (_, i) => i < level ? '●' : '○').join('')}
    </span>
);

const SliderWithDelta = ({ label, value, baseline = 1.0, min, max, step, onChange, accentColor, impact, unit = 'x', disabled, tooltip }) => {
    const delta = value - baseline;
    const deltaPct = baseline !== 0 ? ((delta / baseline) * 100).toFixed(0) : '0';
    const deltaColor = delta > 0 ? '#00dc64' : delta < 0 ? '#ff4444' : '#666';
    return (
        <div>
            <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px', color: 'var(--text-secondary)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Tooltip text={tooltip} position="right">
                        <span style={{ textTransform: 'capitalize', cursor: tooltip ? 'help' : 'default', borderBottom: tooltip ? '1px dotted rgba(255,255,255,0.2)' : 'none' }}>{label}</span>
                    </Tooltip>
                    {impact !== undefined && <ImpactDots level={impact} color={accentColor || '#888'} />}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>{typeof value === 'number' ? value.toFixed(unit === '°C' ? 1 : 2) : value}{unit}</span>
                    {delta !== 0 && (
                        <span style={{ fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: deltaColor, fontWeight: 700 }}>
                            ({delta > 0 ? '+' : ''}{deltaPct}%)
                        </span>
                    )}
                </div>
            </label>
            <input
                type="range" min={min} max={max} step={step} value={value}
                onChange={onChange} disabled={disabled}
                style={{ width: '100%', accentColor: accentColor || '#888' }}
            />
        </div>
    );
};

const ChaosGauge = ({ value }) => {
    const angle = (value / 100) * 240 - 120; // -120 to +120 degrees
    const color = value > 60 ? '#ff4444' : value > 30 ? '#ffc800' : '#00dc64';
    const circumference = 2 * Math.PI * 45;
    const dashOffset = circumference * (1 - (value / 100) * 0.667); // 240deg = 66.7% of circle
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', padding: '16px 0' }}>
            <svg width="140" height="110" viewBox="0 0 140 110">
                {/* Background arc */}
                <circle cx="70" cy="70" r="45" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10"
                    strokeDasharray={`${circumference * 0.667} ${circumference * 0.333}`}
                    strokeLinecap="round" transform="rotate(-210 70 70)" />
                {/* Value arc */}
                <circle cx="70" cy="70" r="45" fill="none" stroke={color} strokeWidth="10"
                    strokeDasharray={`${circumference * 0.667 - dashOffset} ${circumference - (circumference * 0.667 - dashOffset)}`}
                    strokeLinecap="round" transform="rotate(-210 70 70)"
                    style={{ transition: 'stroke-dasharray 0.5s ease, stroke 0.3s ease', filter: `drop-shadow(0 0 6px ${color}60)` }} />
                {/* Center text */}
                <text x="70" y="60" textAnchor="middle" fill={color} fontSize="28" fontWeight="800" fontFamily="var(--font-mono)">{Math.round(value)}</text>
                <text x="70" y="78" textAnchor="middle" fill="#888" fontSize="9" letterSpacing="2" fontWeight="700">CHAOS INDEX</text>
            </svg>
        </div>
    );
};

const WeatherTimeline = ({ totalLaps, rainStartLap, rainProbability, temperature }) => {
    const rainEnd = totalLaps; // rain goes to end for simplicity
    const rainStartPct = (rainStartLap / totalLaps) * 100;
    const tempColor = temperature > 30 ? '#ff6b6b' : temperature > 20 ? '#ffc800' : '#64C4FF';
    return (
        <div style={{ padding: '16px 0' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.65rem', color: '#888', fontFamily: 'var(--font-mono)' }}>
                <span>LAP 1</span>
                <span>LAP {totalLaps}</span>
            </div>
            <div style={{ position: 'relative', height: '36px', borderRadius: '6px', overflow: 'hidden', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                {/* Dry section */}
                <div style={{ position: 'absolute', left: 0, top: 0, width: `${rainStartPct}%`, height: '100%', background: 'linear-gradient(90deg, rgba(255,200,0,0.1) 0%, rgba(255,200,0,0.05) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {rainStartPct > 15 && <span style={{ fontSize: '0.7rem', color: '#ffc800', fontWeight: 700 }}>☀️ DRY</span>}
                </div>
                {/* Rain section */}
                {rainProbability > 0 && (
                    <div style={{ position: 'absolute', left: `${rainStartPct}%`, top: 0, right: 0, height: '100%', background: `linear-gradient(90deg, rgba(100,196,255,${Math.min(0.4, rainProbability * 0.4)}) 0%, rgba(100,196,255,${Math.min(0.25, rainProbability * 0.25)}) 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', borderLeft: '2px dashed rgba(100,196,255,0.4)' }}>
                        <span style={{ fontSize: '0.7rem', color: '#64C4FF', fontWeight: 700 }}>🌧️ {Math.round(rainProbability * 100)}%</span>
                    </div>
                )}
                {/* Lap markers */}
                {[0.25, 0.5, 0.75].map(f => (
                    <div key={f} style={{ position: 'absolute', left: `${f * 100}%`, top: 0, width: '1px', height: '100%', background: 'rgba(255,255,255,0.08)' }} />
                ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.65rem', color: '#888' }}>Rain from Lap {rainStartLap}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '0.65rem', color: '#888' }}>Track Temp:</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tempColor, fontFamily: 'var(--font-mono)' }}>{temperature.toFixed(1)}°C</span>
                </div>
            </div>
        </div>
    );
};


// ===================== MAIN COMPONENT =====================

const ScenarioLaboratory = ({ onSelectScenario, onBackToHome }) => {
    const [activeTab, setActiveTab] = useState('RACE_STRUCTURE');
    const [selectedDriverForEdit, setSelectedDriverForEdit] = useState("VER");
    const [selectedTeamForEdit, setSelectedTeamForEdit] = useState("Red Bull Racing");
    const [config, setConfig] = useState(JSON.parse(JSON.stringify(defaultConfig)));
    const [hoveredTab, setHoveredTab] = useState(null);

    const updateNestedConfig = (section, key, value) => {
        setConfig(prev => ({ ...prev, [section]: { ...prev[section], [key]: value } }));
    };

    // Grid helpers
    const recalculatePositions = (grid) => grid.map((car, idx) => ({ ...car, position: idx + 1 }));
    const handleMoveCarUp = (index) => { if (index === 0) return; const g = [...config.race_structure.grid];[g[index - 1], g[index]] = [g[index], g[index - 1]]; updateNestedConfig('race_structure', 'grid', recalculatePositions(g)); };
    const handleMoveCarDown = (index) => { if (index === config.race_structure.grid.length - 1) return; const g = [...config.race_structure.grid];[g[index + 1], g[index]] = [g[index], g[index + 1]]; updateNestedConfig('race_structure', 'grid', recalculatePositions(g)); };
    const handleRemoveCar = (index) => { const g = config.race_structure.grid.filter((_, i) => i !== index); updateNestedConfig('race_structure', 'grid', recalculatePositions(g)); };
    const handleAddCar = (driverId) => { const d = defaultGrid.find(d => d.driver === driverId); if (!d) return; updateNestedConfig('race_structure', 'grid', recalculatePositions([...config.race_structure.grid, { ...d }])); };
    const availableDriversToAdd = defaultGrid.filter(d => !config.race_structure.grid.some(c => c.driver === d.driver));

    // Preset application
    const applyPreset = (preset) => {
        setConfig(prev => {
            const next = JSON.parse(JSON.stringify(prev));
            if (preset.config.race_structure) Object.assign(next.race_structure, preset.config.race_structure);
            if (preset.config.weather) next.weather = { ...next.weather, ...preset.config.weather };
            if (preset.config.engineering) Object.assign(next.engineering, preset.config.engineering);
            if (preset.config.chaos) Object.assign(next.chaos, preset.config.chaos);
            return next;
        });
    };

    // Reset handlers
    const resetSection = (section) => {
        const defaults = JSON.parse(JSON.stringify(defaultConfig));
        setConfig(prev => ({ ...prev, [section]: defaults[section] }));
    };
    const resetAll = () => setConfig(JSON.parse(JSON.stringify(defaultConfig)));

    const handleLaunch = () => onSelectScenario("custom", config);

    // Live preview computations
    const livePreview = useMemo(() => {
        const chaos = config.chaos;
        const chaosIndex = Math.min(100, Math.round(
            ((chaos.incident_frequency + chaos.safety_car_probability + chaos.mechanical_randomness + chaos.ai_irrationality) / 4 - 0.5) / 2.5 * 100
        ));
        const scRisk = Math.min(100, Math.round(chaos.safety_car_probability * 28));
        const rainProb = config.weather.timeline[0]?.rain_probability || 0;
        const leader = config.race_structure.grid[0]?.driver || 'VER';
        const tireDeg = config.engineering.tire_deg_multiplier;

        let volatility = 'LOW';
        if (chaosIndex > 60 || rainProb > 0.5) volatility = 'HIGH';
        else if (chaosIndex > 30 || rainProb > 0.2) volatility = 'MODERATE';

        return { chaosIndex, scRisk, leader, volatility, rainProb: Math.round(rainProb * 100), tireDeg };
    }, [config]);

    const activeCategory = CATEGORIES.find(c => c.id === activeTab);

    return (
        <div className="scenario-library-container" style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto', color: 'white', position: 'relative' }}>

            {/* ========= LIVE IMPACT PREVIEW (Floating) ========= */}
            <div style={{
                position: 'sticky', top: '12px', float: 'right', zIndex: 50,
                background: 'rgba(10,10,16,0.95)', border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '10px', padding: '12px 16px', minWidth: '200px',
                backdropFilter: 'blur(10px)', boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
            }}>
                <div style={{ fontSize: '0.55rem', color: '#888', letterSpacing: '2px', fontWeight: 700, marginBottom: '8px' }}>LIVE PREVIEW</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                        <span style={{ color: '#888' }}>Leader</span>
                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff' }}>{livePreview.leader}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                        <span style={{ color: '#888' }}>Volatility</span>
                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: livePreview.volatility === 'HIGH' ? '#ff4444' : livePreview.volatility === 'MODERATE' ? '#ffc800' : '#00dc64' }}>{livePreview.volatility}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                        <span style={{ color: '#888' }}>SC Risk</span>
                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: livePreview.scRisk > 50 ? '#ff4444' : '#ffc800' }}>{livePreview.scRisk}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                        <span style={{ color: '#888' }}>Rain</span>
                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: livePreview.rainProb > 40 ? '#64C4FF' : '#888' }}>{livePreview.rainProb}%</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem' }}>
                        <span style={{ color: '#888' }}>Chaos</span>
                        <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: livePreview.chaosIndex > 60 ? '#ff4444' : livePreview.chaosIndex > 30 ? '#ffc800' : '#00dc64' }}>{livePreview.chaosIndex}/100</span>
                    </div>
                </div>
            </div>

            {/* ========= HEADER ========= */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <div>
                    <button onClick={onBackToHome} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', marginBottom: '8px', fontSize: '0.9rem' }}>← BACK TO HOME</button>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 800, margin: 0, background: 'linear-gradient(90deg, #fff, #888)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        SCENARIO LABORATORY
                    </h1>
                    <p style={{ color: 'var(--text-tertiary)', letterSpacing: '2px', textTransform: 'uppercase', fontSize: '0.8rem', marginTop: '4px' }}>
                        Parameter-Driven Scenario Construction
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <Tooltip text={TOOLTIPS.reset_all} position="bottom"><button onClick={resetAll} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#888', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700, letterSpacing: '1px' }}>⟲ RESET ALL</button></Tooltip>
                    <Tooltip text={TOOLTIPS.launch} position="bottom">
                        <button
                            onClick={handleLaunch}
                            className="launch-btn"
                            style={{
                                background: 'var(--red)', color: 'white', border: 'none',
                                padding: '14px 36px', borderRadius: '6px', fontWeight: 700,
                                cursor: 'pointer', textTransform: 'uppercase', letterSpacing: '1px',
                                boxShadow: '0 0 20px rgba(225, 6, 0, 0.4)', fontSize: '0.9rem',
                                transition: 'all 0.3s ease', position: 'relative', overflow: 'hidden',
                            }}
                        >
                            LAUNCH SIMULATION →
                        </button>
                    </Tooltip>
                </div>
            </div>

            {/* ========= PRESET CHIPS ========= */}
            <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.65rem', color: '#666', letterSpacing: '1px', fontWeight: 700, alignSelf: 'center', marginRight: '4px' }}>PRESETS</span>
                {PRESETS.map(p => (
                    <Tooltip key={p.id} text={TOOLTIPS[p.id]} position="bottom">
                        <button onClick={() => applyPreset(p)} style={{
                            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
                            color: '#ccc', padding: '6px 14px', borderRadius: '20px', cursor: 'pointer',
                            fontSize: '0.72rem', fontWeight: 600, transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                        }}
                            onMouseEnter={e => { e.target.style.background = 'rgba(255,255,255,0.1)'; e.target.style.borderColor = 'rgba(255,255,255,0.3)'; }}
                            onMouseLeave={e => { e.target.style.background = 'rgba(255,255,255,0.04)'; e.target.style.borderColor = 'rgba(255,255,255,0.1)'; }}
                        >
                            {p.label}
                        </button>
                    </Tooltip>
                ))}
            </div>

            {/* ========= MAIN LAYOUT ========= */}
            <div style={{ display: 'flex', gap: '32px' }}>

                {/* ===== SIDEBAR NAV ===== */}
                <div style={{ width: '260px', display: 'flex', flexDirection: 'column', gap: '4px', flexShrink: 0 }}>
                    {CATEGORIES.map(cat => {
                        const isActive = activeTab === cat.id;
                        const isHovered = hoveredTab === cat.id;
                        return (
                            <button
                                key={cat.id}
                                onClick={() => setActiveTab(cat.id)}
                                onMouseEnter={() => setHoveredTab(cat.id)}
                                onMouseLeave={() => setHoveredTab(null)}
                                style={{
                                    background: isActive ? 'rgba(255,255,255,0.06)' : isHovered ? 'rgba(255,255,255,0.03)' : 'transparent',
                                    border: 'none',
                                    borderLeft: isActive ? `3px solid ${cat.color}` : '3px solid transparent',
                                    padding: '12px 16px',
                                    borderRadius: '0 8px 8px 0',
                                    color: isActive ? 'white' : isHovered ? '#ccc' : 'var(--text-tertiary)',
                                    textAlign: 'left', cursor: 'pointer',
                                    transition: 'all 0.25s ease',
                                    boxShadow: isActive ? `inset 0 0 20px rgba(${cat.color === '#E74C3C' ? '231,76,60' : '255,255,255'},0.03)` : 'none',
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <span style={{ fontSize: '1.1rem' }}>{cat.icon}</span>
                                    <div>
                                        <div style={{ fontSize: '0.85rem', fontWeight: 700 }}>{cat.label}</div>
                                        <div style={{ fontSize: '0.6rem', color: isActive ? '#888' : '#555', marginTop: '2px', lineHeight: 1.3 }}>{cat.desc}</div>
                                    </div>
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* ===== WORKING AREA ===== */}
                <div style={{ flex: 1, background: 'rgba(20, 24, 32, 0.4)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '32px', position: 'relative' }}>

                    {/* Section header with reset */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
                        <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span>{activeCategory?.icon}</span> {activeCategory?.label}
                        </h2>
                        <Tooltip text={TOOLTIPS.reset_section} position="left">
                            <button onClick={() => resetSection(activeTab === 'RACE_STRUCTURE' ? 'race_structure' : activeTab.toLowerCase())}
                                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', color: '#888', padding: '5px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.65rem', fontWeight: 700, letterSpacing: '1px' }}>
                                ⟲ RESET
                            </button>
                        </Tooltip>
                    </div>

                    {/* ===== RACE STRUCTURE ===== */}
                    {activeTab === 'RACE_STRUCTURE' && (
                        <div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
                                <div>
                                    <Tooltip text={TOOLTIPS.track_selection} position="bottom"><label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)', width: 'fit-content' }}>Track Selection</label></Tooltip>
                                    <select value={config.race_structure.track_id} onChange={(e) => updateNestedConfig('race_structure', 'track_id', e.target.value)}
                                        style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}>
                                        <optgroup label="Middle East">
                                            <option value="bahrain">🇧🇭 Bahrain</option><option value="jeddah">🇸🇦 Jeddah</option>
                                            <option value="qatar">🇶🇦 Qatar</option><option value="abu_dhabi">🇦🇪 Abu Dhabi</option>
                                        </optgroup>
                                        <optgroup label="Europe">
                                            <option value="monaco">🇲🇨 Monaco</option><option value="monza">🇮🇹 Monza</option>
                                            <option value="imola">🇮🇹 Imola</option><option value="spa">🇧🇪 Spa</option>
                                            <option value="silverstone">🇬🇧 Silverstone</option><option value="barcelona">🇪🇸 Barcelona</option>
                                            <option value="spielberg">🇦🇹 Spielberg</option><option value="budapest">🇭🇺 Budapest</option>
                                            <option value="zandvoort">🇳🇱 Zandvoort</option><option value="baku">🇦🇿 Baku</option>
                                        </optgroup>
                                        <optgroup label="Asia-Pacific">
                                            <option value="melbourne">🇦🇺 Melbourne</option><option value="suzuka">🇯🇵 Suzuka</option>
                                            <option value="shanghai">🇨🇳 Shanghai</option><option value="singapore">🇸🇬 Singapore</option>
                                        </optgroup>
                                        <optgroup label="Americas">
                                            <option value="austin">🇺🇸 COTA</option><option value="miami">🇺🇸 Miami</option>
                                            <option value="vegas">🇺🇸 Las Vegas</option><option value="montreal">🇨🇦 Montreal</option>
                                            <option value="mexico">🇲🇽 Mexico City</option><option value="interlagos">🇧🇷 Interlagos</option>
                                        </optgroup>
                                    </select>
                                </div>
                                <div>
                                    <Tooltip text={TOOLTIPS.total_laps} position="bottom"><label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)', cursor: 'help', borderBottom: '1px dotted rgba(255,255,255,0.2)', width: 'fit-content' }}>Total Laps</label></Tooltip>
                                    <input type="number" value={config.race_structure.total_laps}
                                        onChange={(e) => updateNestedConfig('race_structure', 'total_laps', parseInt(e.target.value))}
                                        style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }} />
                                </div>
                                <Tooltip text={TOOLTIPS.safety_car_toggle} position="right">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'help', color: 'var(--text-secondary)' }}>
                                        <input type="checkbox" checked={config.race_structure.sc_enabled} onChange={(e) => updateNestedConfig('race_structure', 'sc_enabled', e.target.checked)} /> Safety Car
                                    </label>
                                </Tooltip>
                                <Tooltip text={TOOLTIPS.drs_toggle} position="right">
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'help', color: 'var(--text-secondary)' }}>
                                        <input type="checkbox" checked={config.race_structure.drs_enabled} onChange={(e) => updateNestedConfig('race_structure', 'drs_enabled', e.target.checked)} /> DRS
                                    </label>
                                </Tooltip>
                            </div>

                            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                Starting Grid
                                <span style={{ fontSize: '0.65rem', color: '#666', fontFamily: 'var(--font-mono)' }}>{config.race_structure.grid.length} drivers</span>
                            </h3>
                            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
                                <div style={{ maxHeight: '350px', overflowY: 'auto', paddingRight: '8px' }}>
                                    {config.race_structure.grid.map((car, idx) => (
                                        <div key={car.driver} style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px', paddingBottom: '6px', borderBottom: idx < config.race_structure.grid.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
                                                <Tooltip text={TOOLTIPS.move_up} position="right"><button onClick={() => handleMoveCarUp(idx)} disabled={idx === 0} style={{ padding: '0 4px', background: 'transparent', border: 'none', color: idx === 0 ? '#333' : '#666', cursor: idx === 0 ? 'not-allowed' : 'pointer', fontSize: '0.7rem' }}>▲</button></Tooltip>
                                                <Tooltip text={TOOLTIPS.move_down} position="right"><button onClick={() => handleMoveCarDown(idx)} disabled={idx === config.race_structure.grid.length - 1} style={{ padding: '0 4px', background: 'transparent', border: 'none', color: idx === config.race_structure.grid.length - 1 ? '#333' : '#666', cursor: idx === config.race_structure.grid.length - 1 ? 'not-allowed' : 'pointer', fontSize: '0.7rem' }}>▼</button></Tooltip>
                                            </div>
                                            <span style={{ width: '28px', fontWeight: 'bold', color: idx < 3 ? 'var(--red)' : 'var(--text-primary)', fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>P{car.position}</span>
                                            <div style={{ width: '4px', height: '22px', borderRadius: '2px', background: TEAM_COLORS[car.team] || '#555' }} />
                                            <span style={{ width: '40px', fontWeight: 700, fontSize: '0.85rem' }}>{car.driver}</span>
                                            <span style={{ color: 'var(--text-tertiary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.8rem' }}>{car.team}</span>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: TIRE_COLORS[car.tire_compound] || '#888' }} />
                                                <select value={car.tire_compound} onChange={(e) => { const g = [...config.race_structure.grid]; g[idx] = { ...g[idx], tire_compound: e.target.value }; updateNestedConfig('race_structure', 'grid', g); }}
                                                    style={{ background: 'rgba(0,0,0,0.5)', color: '#888', border: '1px solid #333', borderRadius: '4px', padding: '3px 4px', fontSize: '0.7rem' }}>
                                                    <option value="SOFT">S</option><option value="MEDIUM">M</option><option value="HARD">H</option><option value="INTERMEDIATE">I</option><option value="WET">W</option>
                                                </select>
                                            </div>
                                            <Tooltip text={TOOLTIPS.remove_driver} position="left"><button onClick={() => handleRemoveCar(idx)} style={{ padding: '3px 6px', background: 'rgba(225,6,0,0.08)', border: '1px solid rgba(225,6,0,0.2)', color: 'var(--red)', borderRadius: '4px', cursor: 'pointer', fontSize: '0.65rem', fontWeight: 'bold' }}>✕</button></Tooltip>
                                        </div>
                                    ))}
                                </div>
                                {availableDriversToAdd.length > 0 && (
                                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px dashed #333', display: 'flex', gap: '12px', alignItems: 'center' }}>
                                        <select id="add-driver-select" style={{ flex: 1, padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}>
                                            {availableDriversToAdd.map(d => <option key={d.driver} value={d.driver}>{d.driver} ({d.team})</option>)}
                                        </select>
                                        <Tooltip text={TOOLTIPS.add_driver} position="top"><button onClick={() => { const s = document.getElementById('add-driver-select'); if (s) handleAddCar(s.value); }}
                                            style={{ padding: '8px 16px', background: 'var(--cyan)', border: 'none', color: '#000', borderRadius: '4px', fontWeight: 'bold', cursor: 'pointer', fontSize: '0.75rem' }}>+ ADD</button></Tooltip>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ===== CHAOS ENGINE ===== */}
                    {activeTab === 'CHAOS' && (
                        <div>
                            <ChaosGauge value={livePreview.chaosIndex} />
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '16px' }}>
                                <SliderWithDelta label="Incident Frequency" value={config.chaos.incident_frequency} min={0} max={3} step={0.1} accentColor="#E74C3C" impact={IMPACT.incident_frequency} tooltip={TOOLTIPS.incident_frequency}
                                    onChange={(e) => updateNestedConfig('chaos', 'incident_frequency', parseFloat(e.target.value))} />
                                <SliderWithDelta label="Safety Car Probability" value={config.chaos.safety_car_probability} min={0} max={3} step={0.1} accentColor="#E74C3C" impact={IMPACT.safety_car_probability} tooltip={TOOLTIPS.safety_car_probability}
                                    onChange={(e) => updateNestedConfig('chaos', 'safety_car_probability', parseFloat(e.target.value))} />
                                <SliderWithDelta label="Mechanical Randomness" value={config.chaos.mechanical_randomness} min={0} max={3} step={0.1} accentColor="#E74C3C" impact={IMPACT.mechanical_randomness} tooltip={TOOLTIPS.mechanical_randomness}
                                    onChange={(e) => updateNestedConfig('chaos', 'mechanical_randomness', parseFloat(e.target.value))} />
                                <SliderWithDelta label="AI Irrationality" value={config.chaos.ai_irrationality} min={0} max={3} step={0.1} accentColor="#E74C3C" impact={IMPACT.ai_irrationality} tooltip={TOOLTIPS.ai_irrationality}
                                    onChange={(e) => updateNestedConfig('chaos', 'ai_irrationality', parseFloat(e.target.value))} />
                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}><span>Random Seed</span></label>
                                    <input type="number" value={config.seed} onChange={(e) => setConfig(prev => ({ ...prev, seed: parseInt(e.target.value) }))}
                                        style={{ width: '100px', padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }} />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ===== WEATHER ===== */}
                    {activeTab === 'WEATHER' && (
                        <div>
                            <WeatherTimeline
                                totalLaps={config.race_structure.total_laps}
                                rainStartLap={config.weather.timeline[0].start_lap}
                                rainProbability={config.weather.timeline[0].rain_probability}
                                temperature={config.weather.timeline[0].temperature}
                            />
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '24px' }}>
                                <SliderWithDelta label="Rain Start Lap" value={config.weather.timeline[0].start_lap} baseline={0} min={0} max={config.race_structure.total_laps} step={1} accentColor="#64C4FF" unit="" tooltip={TOOLTIPS.rain_start}
                                    onChange={(e) => { const t = [...config.weather.timeline]; t[0] = { ...t[0], start_lap: parseInt(e.target.value) }; updateNestedConfig('weather', 'timeline', t); }} />
                                <SliderWithDelta label="Rain Probability" value={config.weather.timeline[0].rain_probability} baseline={0} min={0} max={1} step={0.05} accentColor="#64C4FF" unit="" tooltip={TOOLTIPS.rain_probability}
                                    onChange={(e) => { const t = [...config.weather.timeline]; t[0] = { ...t[0], rain_probability: parseFloat(e.target.value) }; updateNestedConfig('weather', 'timeline', t); }} />
                                <SliderWithDelta label="Temperature" value={config.weather.timeline[0].temperature} baseline={25} min={10} max={40} step={0.5} accentColor="#ffc800" unit="°C" tooltip={TOOLTIPS.temperature}
                                    onChange={(e) => { const t = [...config.weather.timeline]; t[0] = { ...t[0], temperature: parseFloat(e.target.value) }; updateNestedConfig('weather', 'timeline', t); }} />
                            </div>
                        </div>
                    )}

                    {/* ===== ENGINEERING ===== */}
                    {activeTab === 'ENGINEERING' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                            {[
                                { key: 'downforce_level', label: 'Downforce Level', color: '#3498DB' },
                                { key: 'drag_coefficient', label: 'Drag Coefficient', color: '#2ECC71' },
                                { key: 'tire_deg_multiplier', label: 'Tire Degradation', color: '#E74C3C' },
                            ].map(({ key, label, color }) => (
                                <SliderWithDelta key={key} label={label} value={config.engineering[key]} min={0.5} max={1.5} step={0.05} accentColor={color} impact={IMPACT[key]} tooltip={TOOLTIPS[key]}
                                    onChange={(e) => updateNestedConfig('engineering', key, parseFloat(e.target.value))} />
                            ))}
                        </div>
                    )}

                    {/* ===== TEAMS ===== */}
                    {activeTab === 'TEAMS' && (
                        <div>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Select Team</label>
                                <select value={selectedTeamForEdit} onChange={(e) => setSelectedTeamForEdit(e.target.value)}
                                    style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: `1px solid ${TEAM_COLORS[selectedTeamForEdit] || '#333'}40`, color: 'white', borderRadius: '4px' }}>
                                    {[...new Set(config.race_structure.grid.map(c => c.team))].map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                {[
                                    { key: 'engine_power', label: 'Engine Power', color: '#3498DB' },
                                    { key: 'aero_efficiency', label: 'Aero Efficiency', color: '#2ECC71' },
                                    { key: 'pit_stop_speed', label: 'Pit Stop Speed', color: '#ffc800' },
                                    { key: 'reliability', label: 'Reliability', color: '#E74C3C' },
                                ].map(({ key, label, color }) => {
                                    const val = config.teams[selectedTeamForEdit]?.[key] ?? 1.0;
                                    return (
                                        <SliderWithDelta key={key} label={label} value={val} min={0.5} max={1.5} step={0.05} accentColor={color} impact={IMPACT[key]} tooltip={TOOLTIPS[key]}
                                            onChange={(e) => {
                                                const tc = config.teams[selectedTeamForEdit] || { engine_power: 1.0, aero_efficiency: 1.0, pit_stop_speed: 1.0, reliability: 1.0 };
                                                updateNestedConfig('teams', selectedTeamForEdit, { ...tc, [key]: parseFloat(e.target.value) });
                                            }} />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* ===== DRIVERS ===== */}
                    {activeTab === 'DRIVERS' && (
                        <div>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Select Driver</label>
                                <select value={selectedDriverForEdit} onChange={(e) => setSelectedDriverForEdit(e.target.value)}
                                    style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}>
                                    {config.race_structure.grid.map(c => <option key={c.driver} value={c.driver}>{c.driver} ({c.team})</option>)}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                {[
                                    { key: 'aggression', label: 'Aggression', color: '#E056A0' },
                                    { key: 'risk_tolerance', label: 'Risk Tolerance', color: '#E056A0' },
                                    { key: 'overtake_confidence', label: 'Overtake Confidence', color: '#E056A0' },
                                    { key: 'defensive_skill', label: 'Defensive Skill', color: '#E056A0' },
                                    { key: 'tire_preservation', label: 'Tire Preservation', color: '#E056A0' },
                                ].map(({ key, label, color }) => {
                                    const val = config.drivers[selectedDriverForEdit]?.[key] ?? 1.0;
                                    return (
                                        <SliderWithDelta key={key} label={label} value={val} min={0.5} max={1.5} step={0.05} accentColor={color} impact={IMPACT[key]} tooltip={TOOLTIPS[key]}
                                            onChange={(e) => {
                                                const dc = config.drivers[selectedDriverForEdit] || { aggression: 1.0, risk_tolerance: 1.0, overtake_confidence: 1.0, defensive_skill: 1.0, tire_preservation: 1.0 };
                                                updateNestedConfig('drivers', selectedDriverForEdit, { ...dc, [key]: parseFloat(e.target.value) });
                                            }} />
                                    );
                                })}
                            </div>
                        </div>
                    )}

                </div>
            </div>

            {/* ========= CSS Animations ========= */}
            <style>{`
                .launch-btn:hover {
                    box-shadow: 0 0 30px rgba(225, 6, 0, 0.6), 0 0 60px rgba(225, 6, 0, 0.2) !important;
                    transform: translateY(-1px);
                }
                .launch-btn:active {
                    transform: translateY(0);
                }
                .launch-btn::after {
                    content: '';
                    position: absolute;
                    top: 0; left: -100%;
                    width: 100%; height: 100%;
                    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                    animation: launchShine 3s ease-in-out infinite;
                }
                @keyframes launchShine {
                    0% { left: -100%; }
                    50% { left: 100%; }
                    100% { left: 100%; }
                }
                @keyframes tooltipFadeIn {
                    from { opacity: 0; transform: translateY(4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default ScenarioLaboratory;
