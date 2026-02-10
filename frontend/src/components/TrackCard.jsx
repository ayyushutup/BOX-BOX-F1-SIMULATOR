import React from 'react'

const TrackCard = ({ track, onSelect, chaosLevel }) => {
    console.log("Rendering TrackCard:", track)
    if (!track) return <div className="track-card error">Invalid Track Data</div>

    // Safety checks
    const countryCode = track.country_code ? track.country_code.toLowerCase() : 'xx'
    const flagUrl = `https://flagcdn.com/w160/${countryCode}.png`
    const trackName = track.name ? track.name.replace(" (Synthetic)", "").toUpperCase() : "UNKNOWN"
    const lengthKm = track.length ? (track.length / 1000).toFixed(2) : "0.00"
    const drsCount = track.drs_zones ? track.drs_zones.length : 0

    return (
        <div className="track-card" onClick={() => onSelect(track.id)}>
            {/* Header: Flag + Name */}
            <div className="track-card-header">
                <img src={flagUrl} alt={countryCode} className="track-flag" />
                <h2 className="track-name">{trackName}</h2>
            </div>

            {/* Map Area */}
            <div className="track-card-map">
                <svg viewBox={track.view_box} className="track-svg-static">
                    <path
                        d={track.svg_path}
                        fill="none"
                        stroke="rgba(255,255,255,0.15)"
                        strokeWidth="15"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                    <path
                        d={track.svg_path}
                        fill="none"
                        stroke="rgba(255,255,255,0.5)"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    />
                </svg>
            </div>

            {/* Stats Grid */}
            <div className="track-stats-grid">
                <div className="stat-row">
                    <span className="stat-label">LENGTH</span>
                    <span className="stat-value">{lengthKm} KM</span>
                    {/* Placeholder for small icon if needed */}
                </div>

                <div className="stat-row">
                    <span className="stat-label">DRS ZONES</span>
                    <span className="stat-value">{drsCount}</span>
                </div>

                <div className="stat-row">
                    <span className="stat-label">ABRASION</span>
                    <span className="stat-value">{track.abrasion}</span>
                </div>

                <div className="stat-row">
                    <span className="stat-label">DOWNFORCE</span>
                    <span className="stat-value">{track.downforce}</span>
                </div>

                <div className="stat-row">
                    <span className="stat-label">STREET CIRCUIT</span>
                    <span className="stat-value">{track.is_street_circuit ? "YES" : "NO"}</span>
                </div>
            </div>

            {/* Outcomes Grid */}
            <div className="track-outcomes-header">EXPECTED OUTCOMES</div>
            <div className="track-outcomes-grid">
                <div className="outcome-box">
                    <span className="outcome-label">OVERTAKES</span>
                    <span className="outcome-value">{track.expected_overtakes || 0}</span>
                </div>
                <div className="outcome-box">
                    <span className="outcome-label">SC PROBABILITY</span>
                    <span className="outcome-value">{track.sc_probability || 0}%</span>
                </div>
                <div className="outcome-box">
                    <span className="outcome-label">PIT (LAP)</span>
                    <span className="outcome-value">{track.pit_lap_window || "N/A"}</span>
                </div>
                {/* 4th box is pit window again in mockup? Or maybe "CHAOS"? Mockup shows PIT(LAP) twice or maybe "PIT LOSS"? 
                   Looking at image: Bottom left is "SC PROBABILITY", Bottom right is "PIT(LAP) / LOW)"? 
                   Actally the mockup has:
                   Monza: Overtakes 44, Pit 18, SC 18%, Pit Low?
                   Monaco: Overtakes 2, Pit 34, SC 62%, Pit High?
                   The last one might be Pit Loss or something. 
                   I'll use Pit Window and maybe Pit Time Loss.
                */}
                <div className="outcome-box">
                    <span className="outcome-label">PIT LOSS</span>
                    <span className="outcome-value">~{track.pit_stop_loss}s</span>
                </div>
            </div>
        </div>
    )
}

export default TrackCard
