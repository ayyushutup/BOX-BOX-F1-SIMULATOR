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

function TrackMap({ cars, track, raceControl, mode = 'SPECTATOR' }) {
    const defaultPath = "M 100,200 L 300,200 Q 350,200 350,150 L 350,100 Q 350,50 300,50 L 200,50 Q 150,50 150,100 L 150,150 Q 150,200 100,200 Z"
    const trackPath = track?.svg_path || defaultPath

    const pathRef = React.useRef(null)
    const [pathLength, setPathLength] = React.useState(0)

    React.useEffect(() => {
        if (pathRef.current) {
            setPathLength(pathRef.current.getTotalLength())
        }
    }, [trackPath])

    // Detect battles: cars within 0.8s of each other
    const battleDrivers = React.useMemo(() => {
        const set = new Set()
        if (!cars || cars.length < 2) return set
        const sorted = [...cars].sort((a, b) => a.position - b.position)
        for (let i = 1; i < sorted.length; i++) {
            if (sorted[i].interval !== null && sorted[i].interval < 0.8) {
                set.add(sorted[i].driver)
                set.add(sorted[i - 1].driver)
            }
        }
        return set
    }, [cars])

    // Find fastest lap holder
    const fastestLapDriver = React.useMemo(() => {
        if (!cars?.length) return null
        const withBest = cars.filter(c => c.best_lap_time !== null && c.best_lap_time !== undefined)
        if (!withBest.length) return null
        return withBest.reduce((a, b) => a.best_lap_time < b.best_lap_time ? a : b).driver
    }, [cars])

    // Sector boundary fractions (roughly 33% each if no data)
    const sectorBoundaries = React.useMemo(() => {
        if (!track?.sectors) return [0.33, 0.66]
        const total = track.sectors.reduce((s, sec) => s + sec.length, 0)
        let cumul = 0
        const bounds = []
        for (let i = 0; i < track.sectors.length - 1; i++) {
            cumul += track.sectors[i].length
            bounds.push(cumul / total)
        }
        return bounds
    }, [track])

    const baseRadius = mode === 'ENGINEER' ? 14 : 10
    const leaderRadius = mode === 'ENGINEER' ? 16 : 12

    return (
        <div className="track-container">
            <svg viewBox={track?.view_box || "0 0 500 500"} className="track-svg">
                {/* SVG Defs for effects */}
                <defs>
                    <filter id="drs-glow">
                        <feGaussianBlur stdDeviation="3" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="battle-glow">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="fastest-glow">
                        <feGaussianBlur stdDeviation="5" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                    <filter id="yellow-flag-glow">
                        <feGaussianBlur stdDeviation="6" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Yellow Flag Full Track Pulse */}
                {['YELLOW', 'VSC', 'SAFETY_CAR'].includes(raceControl) && (
                    <path
                        d={trackPath}
                        fill="none"
                        stroke="rgba(255, 214, 0, 0.4)"
                        strokeWidth="24"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        filter="url(#yellow-flag-glow)"
                        className="yellow-flag-pulse"
                    />
                )}

                {/* DRS Zones Highlighting */}
                {pathLength > 0 && track?.drs_zones?.map((zone, i) => {
                    const startLen = zone.start * pathLength
                    const endLen = zone.end * pathLength
                    const length = endLen > startLen ? endLen - startLen : (pathLength - startLen) + endLen
                    const dashArray = `0 ${startLen} ${length} ${pathLength}`
                    return (
                        <path
                            key={`drs-${i}`}
                            d={trackPath}
                            fill="none"
                            stroke="rgba(0, 230, 118, 0.25)"
                            strokeWidth="22"
                            strokeLinecap="round"
                            strokeDasharray={dashArray}
                        />
                    )
                })}

                {/* Track Base */}
                <path
                    d={trackPath}
                    fill="none"
                    stroke={mode === 'ENGINEER' ? '#333' : '#222'}
                    strokeWidth={mode === 'ENGINEER' ? "10" : "20"}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />

                {/* Sector split lines */}
                {pathLength > 0 && sectorBoundaries.map((frac, i) => {
                    const pt = pathRef.current.getPointAtLength(frac * pathLength)
                    return (
                        <g key={`sector-${i}`}>
                            <line
                                x1={pt.x - 8} y1={pt.y - 8}
                                x2={pt.x + 8} y2={pt.y + 8}
                                stroke="rgba(255,255,255,0.2)"
                                strokeWidth="2"
                                strokeDasharray="3 3"
                            />
                            <text x={pt.x + 10} y={pt.y - 4} fontSize="7" fill="rgba(255,255,255,0.3)" fontWeight="600">
                                S{i + 2}
                            </text>
                        </g>
                    )
                })}

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
                {cars.map((car) => {
                    if (!pathLength) return null

                    const point = pathRef.current.getPointAtLength(car.lap_progress * pathLength)
                    const x = point.x
                    const y = point.y

                    const r = car.position === 1 ? leaderRadius : baseRadius
                    const teamColor = TEAM_COLORS[car.team] || 'var(--red)'
                    const inBattle = battleDrivers.has(car.driver)
                    const hasFastest = fastestLapDriver === car.driver
                    const isDrs = car.drs_active

                    // Tire wear ring: goes from green (fresh) → yellow → red (worn)
                    const wearPct = (car.tire_wear || 0) / 100
                    const wearHue = (1 - wearPct) * 120 // 120=green, 60=yellow, 0=red
                    const wearColor = `hsl(${wearHue}, 90%, 50%)`
                    // Circumference for stroke-dasharray trick
                    const wearRadius = r + 4
                    const wearCircumf = 2 * Math.PI * wearRadius
                    const wearDash = wearCircumf * (1 - wearPct) // consumed portion = gap

                    // Determine glow filter
                    let filter = ''
                    if (hasFastest) filter = 'url(#fastest-glow)'
                    else if (isDrs) filter = 'url(#drs-glow)'
                    else if (inBattle) filter = 'url(#battle-glow)'

                    return (
                        <g key={car.driver} style={{ transition: 'all 0.1s linear' }}>
                            {/* Tire wear ring */}
                            <circle
                                cx={x} cy={y} r={wearRadius}
                                fill="none"
                                stroke={wearColor}
                                strokeWidth="2.5"
                                strokeDasharray={`${wearDash} ${wearCircumf}`}
                                strokeDashoffset={wearCircumf * 0.25}
                                opacity="0.7"
                                style={{ transition: 'stroke-dasharray 0.3s, stroke 0.3s' }}
                            />

                            {/* Battle pulse ring */}
                            {inBattle && (
                                <circle
                                    cx={x} cy={y} r={r + 8}
                                    fill="none"
                                    stroke="var(--yellow)"
                                    strokeWidth="1.5"
                                    opacity="0.6"
                                    className="battle-pulse-ring"
                                />
                            )}

                            {/* Fastest lap purple glow ring */}
                            {hasFastest && (
                                <circle
                                    cx={x} cy={y} r={r + 7}
                                    fill="none"
                                    stroke="var(--purple)"
                                    strokeWidth="2"
                                    opacity="0.8"
                                    className="fastest-glow-ring"
                                />
                            )}

                            {/* Main car dot */}
                            <circle
                                cx={x} cy={y} r={r}
                                fill={teamColor}
                                stroke={isDrs ? '#00e676' : 'var(--black)'}
                                strokeWidth={isDrs ? '3' : '2'}
                                filter={filter}
                                className={isDrs ? 'drs-car-dot' : ''}
                            />

                            {/* Position label */}
                            <text
                                x={x} y={y + 4}
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

            <style>{`
                @keyframes yellowPulse {
                    0%, 100% { opacity: 0.3; }
                    50% { opacity: 0.8; }
                }
                .yellow-flag-pulse {
                    animation: yellowPulse 2s ease-in-out infinite;
                }
            `}</style>
        </div>
    )
}

export default TrackMap
