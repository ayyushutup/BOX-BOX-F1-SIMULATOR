import React, { useState } from 'react';

const CATEGORIES = [
    { id: 'RACE_STRUCTURE', label: 'Race Structure', icon: '🏁' },
    { id: 'WEATHER', label: 'Weather Timeline', icon: '🌦️' },
    { id: 'TEAMS', label: 'Team Ratings', icon: '⚙️' },
    { id: 'ENGINEERING', label: 'Car Setup', icon: '🏎️' },
    { id: 'DRIVERS', label: 'Driver Persona', icon: '🧠' },
    { id: 'CHAOS', label: 'Chaos Engine', icon: '🎲' }
];

// Initial Config State Setup
const defaultGrid = [
    { driver: "VER", team: "Red Bull Racing", position: 1, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "NOR", team: "McLaren", position: 2, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "LEC", team: "Ferrari", position: 3, tire_compound: "MEDIUM", fuel_kg: 100 },
    { driver: "HAM", team: "Mercedes", position: 4, tire_compound: "MEDIUM", fuel_kg: 100 },
];

const ScenarioLaboratory = ({ onSelectScenario, onBackToHome }) => {
    const [activeTab, setActiveTab] = useState('RACE_STRUCTURE');
    const [selectedDriverForEdit, setSelectedDriverForEdit] = useState("VER");
    const [selectedTeamForEdit, setSelectedTeamForEdit] = useState("Red Bull Racing");

    const [config, setConfig] = useState({
        race_structure: {
            track_id: "monaco",
            total_laps: 50,
            starting_lap: 0,
            drs_enabled: true,
            sc_enabled: true,
            pit_lane_time_delta: 20.0,
            grid: defaultGrid
        },
        weather: {
            timeline: [{ start_lap: 0, rain_probability: 0.0, temperature: 25.0 }],
        },
        teams: {},
        engineering: {
            downforce_level: 1.0,
            drag_coefficient: 1.0,
            tire_deg_multiplier: 1.0,
        },
        drivers: {},
        chaos: {
            mechanical_randomness: 1.0,
            incident_frequency: 1.0,
            safety_car_probability: 1.0,
            ai_irrationality: 1.0
        },
        seed: 42
    });

    const updateNestedConfig = (section, key, value) => {
        setConfig(prev => ({
            ...prev,
            [section]: {
                ...prev[section],
                [key]: value
            }
        }));
    };

    const handleLaunch = () => {
        // We pass the full JSON object to the parent App.jsx as activeScenario config
        onSelectScenario("custom", config);
    };

    return (
        <div className="scenario-library-container" style={{ padding: '24px', maxWidth: '1600px', margin: '0 auto', color: 'white' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                <div>
                    <button
                        onClick={onBackToHome}
                        style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', marginBottom: '8px', fontSize: '0.9rem' }}
                    >
                        ← BACK TO HOME
                    </button>
                    <h1 style={{ fontSize: '2.5rem', fontWeight: 800, margin: 0, background: 'linear-gradient(90deg, #fff, #888)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                        SCENARIO LABORATORY
                    </h1>
                    <p style={{ color: 'var(--text-tertiary)', letterSpacing: '2px', textTransform: 'uppercase', fontSize: '0.8rem', marginTop: '4px' }}>
                        Parameter-Driven Scenario Construction
                    </p>
                </div>
                <div>
                    <button
                        onClick={handleLaunch}
                        style={{
                            background: 'var(--red)',
                            color: 'white',
                            border: 'none',
                            padding: '12px 32px',
                            borderRadius: '6px',
                            fontWeight: 700,
                            cursor: 'pointer',
                            textTransform: 'uppercase',
                            letterSpacing: '1px',
                            boxShadow: '0 0 20px rgba(225, 6, 0, 0.4)'
                        }}
                    >
                        LAUNCH SIMULATION →
                    </button>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '32px' }}>
                {/* 6-Tier Nav */}
                <div style={{ width: '250px', display: 'flex', flexDirection: 'column', gap: '8px', flexShrink: 0 }}>
                    {CATEGORIES.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => setActiveTab(cat.id)}
                            style={{
                                background: activeTab === cat.id ? 'rgba(255,255,255,0.1)' : 'transparent',
                                border: '1px solid',
                                borderColor: activeTab === cat.id ? 'rgba(255,255,255,0.2)' : 'transparent',
                                padding: '12px 16px',
                                borderRadius: '8px',
                                color: activeTab === cat.id ? 'white' : 'var(--text-tertiary)',
                                textAlign: 'left',
                                cursor: 'pointer',
                                fontSize: '0.9rem',
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                transition: 'all 0.2s'
                            }}
                        >
                            <span>{cat.icon}</span>
                            {cat.label}
                        </button>
                    ))}
                </div>

                {/* Working Area */}
                <div style={{ flex: 1, background: 'rgba(20, 24, 32, 0.4)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '32px' }}>

                    {activeTab === 'RACE_STRUCTURE' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Race Structure</h2>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Track Selection</label>
                                    <select
                                        value={config.race_structure.track_id}
                                        onChange={(e) => updateNestedConfig('race_structure', 'track_id', e.target.value)}
                                        style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}
                                    >
                                        <option value="monaco">Monaco</option>
                                        <option value="monza">Monza</option>
                                        <option value="spa">Spa</option>
                                        <option value="silverstone">Silverstone</option>
                                    </select>
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Total Laps</label>
                                    <input
                                        type="number"
                                        value={config.race_structure.total_laps}
                                        onChange={(e) => updateNestedConfig('race_structure', 'total_laps', parseInt(e.target.value))}
                                        style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}
                                    />
                                </div>

                                <div>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                                        <input
                                            type="checkbox"
                                            checked={config.race_structure.sc_enabled}
                                            onChange={(e) => updateNestedConfig('race_structure', 'sc_enabled', e.target.checked)}
                                        />
                                        Safety Car Enabled
                                    </label>
                                </div>

                                <div>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                                        <input
                                            type="checkbox"
                                            checked={config.race_structure.drs_enabled}
                                            onChange={(e) => updateNestedConfig('race_structure', 'drs_enabled', e.target.checked)}
                                        />
                                        DRS Enabled
                                    </label>
                                </div>
                            </div>

                            <h3 style={{ marginTop: '32px', marginBottom: '16px', color: 'var(--text-secondary)' }}>Starting Grid (Top 4 Preview)</h3>
                            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px' }}>
                                {config.race_structure.grid.map((car, idx) => (
                                    <div key={idx} style={{ display: 'flex', gap: '16px', marginBottom: '8px', paddingBottom: '8px', borderBottom: idx < 3 ? '1px solid rgba(255,255,255,0.05)' : 'none' }}>
                                        <span style={{ width: '30px', fontWeight: 'bold' }}>P{car.position}</span>
                                        <span style={{ width: '60px' }}>{car.driver}</span>
                                        <span style={{ color: 'var(--text-tertiary)' }}>{car.team}</span>
                                    </div>
                                ))}
                                <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '8px' }}>*Grid limits to 4 cars for testing MVP.</p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'CHAOS' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Chaos Engine Config</h2>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Incident Frequency Multiplier</span>
                                        <span>{config.chaos.incident_frequency.toFixed(1)}x</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="3" step="0.1"
                                        value={config.chaos.incident_frequency}
                                        onChange={(e) => updateNestedConfig('chaos', 'incident_frequency', parseFloat(e.target.value))}
                                        style={{ width: '100%' }}
                                    />
                                    <p style={{ fontSize: '0.8rem', color: 'var(--text-tertiary)', marginTop: '4px' }}>Scales the base probability of track-specific incidents happening per tick.</p>
                                </div>

                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Safety Car Probability Multiplier</span>
                                        <span>{config.chaos.safety_car_probability.toFixed(1)}x</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="3" step="0.1"
                                        value={config.chaos.safety_car_probability}
                                        onChange={(e) => updateNestedConfig('chaos', 'safety_car_probability', parseFloat(e.target.value))}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Random Seed</span>
                                    </label>
                                    <input
                                        type="number"
                                        value={config.seed}
                                        onChange={(e) => setConfig(prev => ({ ...prev, seed: parseInt(e.target.value) }))}
                                        style={{ width: '100px', padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'WEATHER' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Weather Timeline</h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Rain Start Lap</span>
                                        <span>{config.weather.timeline[0].start_lap}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max={config.race_structure.total_laps} step="1"
                                        value={config.weather.timeline[0].start_lap}
                                        onChange={(e) => {
                                            const newTimeline = [...config.weather.timeline];
                                            newTimeline[0].start_lap = parseInt(e.target.value);
                                            updateNestedConfig('weather', 'timeline', newTimeline);
                                        }}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Rain Probability</span>
                                        <span>{(config.weather.timeline[0].rain_probability * 100).toFixed(0)}%</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0" max="1.0" step="0.05"
                                        value={config.weather.timeline[0].rain_probability}
                                        onChange={(e) => {
                                            const newTimeline = [...config.weather.timeline];
                                            newTimeline[0].rain_probability = parseFloat(e.target.value);
                                            updateNestedConfig('weather', 'timeline', newTimeline);
                                        }}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)' }}>
                                        <span>Temperature (°C)</span>
                                        <span>{config.weather.timeline[0].temperature.toFixed(1)}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="10" max="40" step="0.5"
                                        value={config.weather.timeline[0].temperature}
                                        onChange={(e) => {
                                            const newTimeline = [...config.weather.timeline];
                                            newTimeline[0].temperature = parseFloat(e.target.value);
                                            updateNestedConfig('weather', 'timeline', newTimeline);
                                        }}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'ENGINEERING' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Car Setup</h2>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                {['downforce_level', 'drag_coefficient', 'tire_deg_multiplier'].map(attr => (
                                    <div key={attr}>
                                        <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                            <span>{attr.replace(/_/g, ' ')}</span>
                                            <span>{config.engineering[attr].toFixed(2)}x</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0.5" max="1.5" step="0.05"
                                            value={config.engineering[attr]}
                                            onChange={(e) => updateNestedConfig('engineering', attr, parseFloat(e.target.value))}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'TEAMS' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Team Ratings</h2>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Select Team</label>
                                <select
                                    value={selectedTeamForEdit}
                                    onChange={(e) => setSelectedTeamForEdit(e.target.value)}
                                    style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}
                                >
                                    {[...new Set(config.race_structure.grid.map(c => c.team))].map(t => (
                                        <option key={t} value={t}>{t}</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                {['engine_power', 'aero_efficiency', 'pit_stop_speed', 'reliability'].map(attr => {
                                    const val = config.teams[selectedTeamForEdit]?.[attr] ?? 1.0;
                                    return (
                                        <div key={attr}>
                                            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                                <span>{attr.replace(/_/g, ' ')}</span>
                                                <span>{val.toFixed(2)}x</span>
                                            </label>
                                            <input
                                                type="range"
                                                min="0.5" max="1.5" step="0.05"
                                                value={val}
                                                onChange={(e) => {
                                                    const teamCfg = config.teams[selectedTeamForEdit] || { engine_power: 1.0, aero_efficiency: 1.0, pit_stop_speed: 1.0, reliability: 1.0 };
                                                    teamCfg[attr] = parseFloat(e.target.value);
                                                    updateNestedConfig('teams', selectedTeamForEdit, teamCfg);
                                                }}
                                                style={{ width: '100%' }}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {activeTab === 'DRIVERS' && (
                        <div>
                            <h2 style={{ margin: '0 0 24px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>Driver Persona</h2>
                            <div style={{ marginBottom: '24px' }}>
                                <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Select Driver</label>
                                <select
                                    value={selectedDriverForEdit}
                                    onChange={(e) => setSelectedDriverForEdit(e.target.value)}
                                    style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', borderRadius: '4px' }}
                                >
                                    {config.race_structure.grid.map(c => (
                                        <option key={c.driver} value={c.driver}>{c.driver} ({c.team})</option>
                                    ))}
                                </select>
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                {['aggression', 'risk_tolerance', 'overtake_confidence', 'defensive_skill', 'tire_preservation'].map(attr => {
                                    const val = config.drivers[selectedDriverForEdit]?.[attr] ?? 1.0;
                                    return (
                                        <div key={attr}>
                                            <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                                                <span>{attr.replace(/_/g, ' ')}</span>
                                                <span>{val.toFixed(2)}x</span>
                                            </label>
                                            <input
                                                type="range"
                                                min="0.5" max="1.5" step="0.05"
                                                value={val}
                                                onChange={(e) => {
                                                    const drvCfg = config.drivers[selectedDriverForEdit] || { aggression: 1.0, risk_tolerance: 1.0, overtake_confidence: 1.0, defensive_skill: 1.0, tire_preservation: 1.0 };
                                                    drvCfg[attr] = parseFloat(e.target.value);
                                                    updateNestedConfig('drivers', selectedDriverForEdit, drvCfg);
                                                }}
                                                style={{ width: '100%' }}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ScenarioLaboratory;
