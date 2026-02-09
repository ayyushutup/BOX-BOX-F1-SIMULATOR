import React from 'react'

// Team colors for F1 teams
const TEAM_COLORS = {
    'Red Bull Racing': '#1E41FF',
    'Ferrari': '#DC0000',
    'Mercedes': '#00D2BE',
    'McLaren': '#FF8700',
    'Aston Martin': '#006F62',
    'Alpine': '#0090FF',
    'Williams': '#005AFF',
    'RB': '#2B4562',
    'Haas': '#B6BABD',
    'Sauber': '#52E252',
}

function TrackMap({ cars, track, mode = 'SPECTATOR' }) {
    // Default fallback path if no track data
    const defaultPath = "M 100,200 L 300,200 Q 350,200 350,150 L 350,100 Q 350,50 300,50 L 200,50 Q 150,50 150,100 L 150,150 Q 150,200 100,200 Z"

    // Use track's SVG path if available
    const trackPath = track?.svg_path || defaultPath

    // Ref to the path element to calculate positions
    const pathRef = React.useRef(null)
    const [pathLength, setPathLength] = React.useState(0)

    // Update path length when track changes
    React.useEffect(() => {
        if (pathRef.current) {
            setPathLength(pathRef.current.getTotalLength())
        }
    }, [trackPath])

    return (
        <div className="track-container">
            <svg viewBox={track?.view_box || "0 0 500 500"} className="track-svg">
                {/* Track Base */}
                <path
                    d={trackPath}
                    fill="none"
                    stroke={mode === 'ENGINEER' ? '#333' : '#222'}
                    strokeWidth={mode === 'ENGINEER' ? "10" : "20"}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />

                {/* Track Center Line */}
                <path
                    ref={pathRef}
                    d={trackPath}
                    fill="none"
                    stroke={mode === 'ENGINEER' ? '#888' : '#fff'}
                    strokeWidth={mode === 'ENGINEER' ? "2" : "5"}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />

                {/* Start/Finish Line Indicator */}
                <path
                    d={trackPath}
                    fill="none"
                    stroke="var(--red)"
                    strokeWidth="20"
                    strokeDasharray="4 10000"
                    strokeDashoffset="2"
                    pathLength="100"
                    className="track-start-line"
                />

                {/* Car positions */}
                {cars.map((car, index) => {
                    if (!pathLength) return null

                    // Calculate position on track based on lap_progress
                    // Adjust point based on path length
                    const point = pathRef.current.getPointAtLength(car.lap_progress * pathLength)
                    const x = point.x
                    const y = point.y

                    return (
                        <g key={car.driver} style={{ transition: 'all 0.1s linear' }}>
                            <circle
                                cx={x}
                                cy={y}
                                r={mode === 'ENGINEER' ? (car.position === 1 ? "16" : "14") : (car.position === 1 ? "12" : "10")}
                                fill={TEAM_COLORS[car.team] || 'var(--red)'}
                                stroke="var(--black)"
                                strokeWidth="2"
                                style={{ zIndex: 20 - car.position }}
                            />
                            <text
                                x={x}
                                y={y + 4}
                                textAnchor="middle"
                                fontSize="8"
                                fontWeight="bold"
                                fill="white"
                            >
                                {car.position}
                            </text>
                        </g>
                    )
                })}
            </svg>

            <div className="track-hud-overlay">
                <div className="track-scale">
                    <div className="scale-bar"></div>
                    <span>1 KM</span>
                </div>
                <div className="sector-hud">
                    <span className="hud-label">CURRENT SECTOR</span>
                    <span className="hud-value">{cars[0]?.sector + 1 || 1}</span>
                </div>
            </div>
        </div>
    )
}

export default TrackMap
