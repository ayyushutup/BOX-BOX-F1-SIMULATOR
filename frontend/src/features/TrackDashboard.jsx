import React from 'react'

const CHAOS_LEVEL_COLORS = {
    low: '#4CAF50',
    medium: '#FFC107',
    high: '#FF5722'
}

function TrackDashboard({ tracks, onSelectTrack }) {
    if (!tracks || tracks.length === 0) {
        return <div className="loading">Loading tracks...</div>
    }

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div>
                    <h1 className="dashboard-title">TRACK SIMULATIONS</h1>
                    <div className="dashboard-subtitle">SELECT A CIRCUIT TO BEGIN</div>
                </div>
                <div className="chaos-indicator">
                    <span>TRACK SIMULATION<br />CHAOS LEVEL</span>
                    <div className="chaos-value" style={{ backgroundColor: '#FFD700' }}>
                        32%
                    </div>
                </div>
            </header>

            <div className="tracks-grid">
                {tracks.map(track => (
                    <div key={track.id} className="track-card" onClick={() => onSelectTrack(track.id)}>
                        <div className="track-card-header">
                            <span className="track-flag">
                                {track.id === 'monaco' ? '🇲🇨' :
                                    track.id === 'monza' ? '🇮🇹' :
                                        track.id === 'silverstone' ? '🇬🇧' :
                                            track.id === 'spa' ? '🇧🇪' : '🏁'}
                            </span>
                            <span className="track-name">{track.name.split(' (')[0].toUpperCase()}</span>
                        </div>

                        <div className="track-card-map">
                            <svg viewBox="0 0 500 500" className="dashboard-track-svg">
                                <path
                                    d={track.svg_path}
                                    fill="none"
                                    stroke="var(--black)"
                                    strokeWidth="15"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </div>

                        <div className="track-stats">
                            <div className="stat-row header-row">
                                <span>LENGTH</span>
                                <span>{(track.length / 1000).toFixed(2)} KM</span>
                            </div>
                            <div className="stat-row">
                                <span>DRS ZONES</span>
                                <span>{track.drs_zones?.length || 0}</span>
                            </div>
                            <div className="stat-row">
                                <span>ABRASION</span>
                                <span>{track.abrasion || 'MEDIUM'}</span>
                            </div>
                            <div className="stat-row">
                                <span>DOWNFORCE</span>
                                <span>{track.downforce || 'MEDIUM'}</span>
                            </div>
                            <div className="stat-row">
                                <span>STREET CIRCUIT</span>
                                <span>{track.is_street_circuit ? 'YES' : 'NO'}</span>
                            </div>
                        </div>

                        <div className="track-outcomes">
                            <div className="outcome-title">EXPECTED OUTCOMES</div>
                            <div className="outcome-grid">
                                <div className="outcome-item">
                                    <span className="outcome-label">OVERTAKES</span>
                                    <span className="outcome-value">{track.expected_overtakes || '-'}</span>
                                </div>
                                <div className="outcome-item">
                                    <span className="outcome-label">PIT (LAP)</span>
                                    <span className="outcome-value">{track.pit_stop_loss || 20}s</span>
                                </div>
                                <div className="outcome-item">
                                    <span className="outcome-label">SC PROB</span>
                                    <span className="outcome-value">{track.sc_probability || 0}%</span>
                                </div>
                                <div className="outcome-item">
                                    <span className="outcome-label">CHAOS</span>
                                    <span className="outcome-value">{track.chaos_level || 0}%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default TrackDashboard
