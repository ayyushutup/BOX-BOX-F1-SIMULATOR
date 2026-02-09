import React, { useState } from 'react'
import TrackCard from '../components/TrackCard'

const TrackSelection = ({ tracks, onSelectTrack }) => {
    // Determine overall chaos level from the "selected" track or average?
    // The mockup shows 32% in a big yellow box. I'll just use the last track's chaos or a default.
    // Or maybe it updates on hover? Let's make it interactive!
    const [hoveredTrack, setHoveredTrack] = useState(null)

    // Default to Silverstone's level if nothing hovered (matching mockup)
    // Finding Silverstone or fallback to 0
    const defaultChaos = tracks.find(t => t.id === 'silverstone_synthetic')?.chaos_level || 32
    const currentChaos = hoveredTrack ? hoveredTrack.chaos_level : defaultChaos

    return (
        <div className="track-selection-container">
            {/* Top Bar: Title + Lap Time Chart */}
            <div className="track-selection-header">
                <h1 className="main-title">TRACK SIMULATIONS</h1>

                <div className="lap-time-chart">
                    <span className="chart-title">AVERAGE LAP TIME</span>
                    <div className="chart-bars">
                        {/* Mock bars for visual matching */}
                        <div className="bar bar-red" style={{ width: '40%' }}></div>
                        <div className="bar bar-yellow" style={{ width: '65%' }}></div>
                        <div className="bar bar-blue" style={{ width: '85%' }}></div>
                    </div>
                </div>
            </div>

            {/* Grid of Tracks */}
            <div className="track-grid">
                {tracks.map(track => (
                    <div
                        key={track.id}
                        onMouseEnter={() => setHoveredTrack(track)}
                        onMouseLeave={() => setHoveredTrack(null)}
                    >
                        <TrackCard
                            track={track}
                            onSelect={onSelectTrack}
                        />
                    </div>
                ))}
            </div>

            {/* Bottom Bar: Stats?? Actually it's part of the grid in mockup */}
            {/* The mockup has the chaos level box in the bottom right corner of the LAYOUT, 
                but it looks like it might be a footer or just part of the grid flow.
                I'll place it as a footer section. */}
            <div className="track-selection-footer">
                <div className="chaos-box">
                    <div className="chaos-label">
                        TRACK SIMULATION<br />CHAOS LEVEL
                        <div className="chaos-squares">
                            {/* 7 squares */}
                            {[...Array(7)].map((_, i) => (
                                <div key={i} className={`square ${i < Math.ceil(currentChaos / 15) ? 'filled' : ''}`}></div>
                            ))}
                        </div>
                    </div>
                    <div className="chaos-value">{currentChaos}%</div>
                </div>
            </div>
        </div>
    )
}

export default TrackSelection
