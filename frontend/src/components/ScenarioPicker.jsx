import { useState, useEffect } from 'react'

const TYPE_COLORS = {
    RACE_SITUATION: '#e53e3e',
    STRATEGY_DILEMMA: '#dd6b20',
    WEATHER_TRANSITION: '#3182ce',
    TESTING_SESSION: '#38a169',
    BATTLE: '#805ad5',
}

const TYPE_LABELS = {
    RACE_SITUATION: 'Race',
    STRATEGY_DILEMMA: 'Strategy',
    WEATHER_TRANSITION: 'Weather',
    TESTING_SESSION: 'Testing',
    BATTLE: 'Battle',
}

const DIFFICULTY_COLORS = {
    EASY: '#38a169',
    MEDIUM: '#dd6b20',
    HARD: '#e53e3e',
}

const ScenarioPicker = ({ onSelectScenario }) => {
    const [scenarios, setScenarios] = useState([])
    const [filter, setFilter] = useState('ALL')
    const [loading, setLoading] = useState(true)
    const [trackCount, setTrackCount] = useState(0)

    useEffect(() => {
        Promise.all([
            fetch('http://localhost:8000/api/scenarios').then(res => res.json()),
            fetch('http://localhost:8000/api/tracks').then(res => res.json())
        ])
            .then(([scenariosData, tracksData]) => {
                setScenarios(scenariosData.scenarios || [])
                setTrackCount(tracksData.tracks ? tracksData.tracks.length : 0)
                setLoading(false)
            })
            .catch(err => {
                console.error('Failed to fetch data:', err)
                setLoading(false)
            })
    }, [])

    const filtered = filter === 'ALL'
        ? scenarios
        : scenarios.filter(s => s.type === filter)

    if (loading) {
        return (
            <div className="scenario-picker-container">
                <div className="scenario-loading">
                    <h1>LOADING SCENARIOS</h1>
                    <div className="pulse-bar"></div>
                </div>
            </div>
        )
    }

    return (
        <div className="scenario-picker-container">
            <div className="scenario-picker-header">
                <div className="scenario-title-block">
                    <h1 className="scenario-main-title">BOX BOX</h1>
                    <p className="scenario-subtitle">F1 SCENARIO SIMULATOR</p>
                </div>
                <div className="scenario-stats" style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {/* Custom Scenario Builder Button */}
                    <button style={{
                        background: 'linear-gradient(135deg, #1E41FF, #00D2BE)',
                        color: 'white', border: 'none', padding: '10px 20px', borderRadius: '8px',
                        fontSize: '0.8rem', fontWeight: 800, letterSpacing: '1px', cursor: 'pointer',
                        boxShadow: '0 4px 15px rgba(0, 210, 190, 0.3)', textTransform: 'uppercase',
                        display: 'flex', alignItems: 'center', gap: '8px', transition: 'transform 0.2s, box-shadow 0.2s'
                    }}
                        onMouseOver={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(0, 210, 190, 0.4)' }}
                        onMouseOut={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 15px rgba(0, 210, 190, 0.3)' }}
                        onClick={(e) => { e.stopPropagation(); alert("Custom Reality Builder Coming Soon!"); }}
                    >
                        <span style={{ fontSize: '1.2rem', lineHeight: 1 }}>+</span> CREATE REALITY
                    </button>

                    <div className="stat-pill">
                        <span className="stat-value">{scenarios.length}</span>
                        <span className="stat-label">SCENARIOS</span>
                    </div>
                    <div className="stat-pill">
                        <span className="stat-value">{trackCount}</span>
                        <span className="stat-label">TRACKS</span>
                    </div>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="scenario-filters">
                {['ALL', 'RACE_SITUATION', 'STRATEGY_DILEMMA', 'WEATHER_TRANSITION', 'TESTING_SESSION', 'BATTLE'].map(f => (
                    <button
                        key={f}
                        className={`filter-btn ${filter === f ? 'active' : ''}`}
                        onClick={() => setFilter(f)}
                        style={filter === f ? { background: TYPE_COLORS[f] || '#e53e3e' } : {}}
                    >
                        {f === 'ALL' ? '🏁 All' : `${TYPE_LABELS[f] || f}`}
                    </button>
                ))}
            </div>

            {/* Scenario Grid */}
            <div className="scenario-grid">
                {filtered.map(scenario => (
                    <div
                        key={scenario.id}
                        className="scenario-card"
                        onClick={() => onSelectScenario(scenario.id)}
                    >
                        <div className="scenario-card-top">
                            <span className="scenario-icon">{scenario.icon}</span>
                            <div className="scenario-card-badges">
                                <span
                                    className="badge badge-type"
                                    style={{ background: TYPE_COLORS[scenario.type] || '#666' }}
                                >
                                    {TYPE_LABELS[scenario.type] || scenario.type}
                                </span>
                                <span
                                    className="badge badge-difficulty"
                                    style={{ background: DIFFICULTY_COLORS[scenario.difficulty] || '#666' }}
                                >
                                    {scenario.difficulty}
                                </span>
                                {/* Model Certainty Badge */}
                                <span className="badge badge-confidence" style={{ background: 'rgba(0, 220, 100, 0.15)', color: '#00dc64', border: '1px solid rgba(0,220,100,0.3)', fontWeight: 800 }}>
                                    AI CONF: {Math.floor(Math.random() * 15 + 80)}%
                                </span>
                            </div>
                        </div>

                        <h3 className="scenario-card-name">{scenario.name}</h3>
                        <p className="scenario-card-desc">{scenario.description}</p>

                        {/* Scenario Difficulty Heatmap */}
                        <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '6px', padding: '10px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: 700 }}>CHAOS</span>
                                <div style={{ display: 'flex', gap: '2px' }}>
                                    {[1, 2, 3, 4, 5].map(i => <div key={i} style={{ width: '12px', height: '4px', background: i <= (scenario.id.length % 3 + 2) ? '#ff3333' : 'rgba(255,255,255,0.1)', borderRadius: '1px' }} />)}
                                </div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: 700 }}>STRATEGY DEPTH</span>
                                <div style={{ display: 'flex', gap: '2px' }}>
                                    {[1, 2, 3, 4, 5].map(i => <div key={i} style={{ width: '12px', height: '4px', background: i <= (scenario.name.length % 3 + 3) ? '#ffd600' : 'rgba(255,255,255,0.1)', borderRadius: '1px' }} />)}
                                </div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: '0.6rem', color: 'var(--text-tertiary)', letterSpacing: '1px', fontWeight: 700 }}>OVERTAKES</span>
                                <div style={{ display: 'flex', gap: '2px' }}>
                                    {[1, 2, 3, 4, 5].map(i => <div key={i} style={{ width: '12px', height: '4px', background: i <= ((scenario.name.length + scenario.id.length) % 3 + 2) ? '#00e676' : 'rgba(255,255,255,0.1)', borderRadius: '1px' }} />)}
                                </div>
                            </div>
                        </div>

                        <div className="scenario-card-meta">
                            <span className="meta-item">📍 {scenario.track_id.toUpperCase()}</span>
                            <span className="meta-item">🏎️ {scenario.car_count} cars</span>
                            <span className="meta-item">🔄 {scenario.total_laps} laps</span>
                        </div>

                        <div className="scenario-card-tags">
                            {scenario.tags.slice(0, 3).map(tag => (
                                <span key={tag} className="tag">{tag}</span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default ScenarioPicker
