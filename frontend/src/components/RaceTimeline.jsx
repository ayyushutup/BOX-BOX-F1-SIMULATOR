
import React, { useCallback } from 'react';

const RaceTimeline = ({ totalLaps, currentLap, events, onSkipToLap }) => {
    if (!totalLaps) return null;

    const timelineEvents = events.filter(e =>
        ['SAFETY_CAR', 'VIRTUAL_SAFETY_CAR', 'RED_FLAG', 'PIT_STOP', 'DNF', 'WEATHER_CHANGE', 'OVERTAKE'].includes(e.type || e.event_type)
    );

    const getEventIcon = (type) => {
        switch (type) {
            case 'SAFETY_CAR': return '🚗';
            case 'VIRTUAL_SAFETY_CAR': case 'VSC': return '⚠️';
            case 'RED_FLAG': return '🚩';
            case 'PIT_STOP': return '🛞';
            case 'DNF': return '❌';
            case 'OVERTAKE': return '⚔️';
            case 'WEATHER_CHANGE': return '🌧';
            default: return '•';
        }
    };

    const handleClick = useCallback((e) => {
        if (!onSkipToLap) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const pct = x / rect.width;
        const lap = Math.max(1, Math.min(totalLaps, Math.round(pct * totalLaps)));
        onSkipToLap(lap);
    }, [onSkipToLap, totalLaps]);

    const progressPct = (currentLap / totalLaps) * 100;

    return (
        <div style={{
            width: '100%', background: 'rgba(10,12,18,0.9)', backdropFilter: 'blur(12px)',
            border: '1px solid var(--glass-border)', borderRadius: '10px',
            padding: '14px 16px', position: 'relative', height: '80px',
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
        }}>
            {/* Title */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-tertiary)', letterSpacing: '2px' }}>RACE TIMELINE</span>
                <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                    LAP {currentLap} / {totalLaps}
                </span>
            </div>

            {/* Clickable Track */}
            <div
                style={{
                    position: 'relative', width: '100%', height: '10px',
                    background: 'rgba(255,255,255,0.06)', borderRadius: '5px',
                    cursor: onSkipToLap ? 'pointer' : 'default',
                    transition: 'height 0.2s',
                }}
                onClick={handleClick}
                title={onSkipToLap ? 'Click to jump to lap' : undefined}
            >
                {/* Progress fill */}
                <div style={{
                    position: 'absolute', top: 0, left: 0, height: '100%',
                    width: `${progressPct}%`,
                    background: 'linear-gradient(90deg, rgba(225,6,0,0.3), var(--red))',
                    borderRadius: '5px', transition: 'width 0.3s linear',
                }} />

                {/* Event markers */}
                {timelineEvents.map((e, i) => {
                    const leftPos = (e.lap / totalLaps) * 100;
                    return (
                        <div
                            key={i}
                            style={{
                                position: 'absolute', top: '50%', transform: 'translateY(-50%)',
                                left: `${leftPos}%`, display: 'flex', flexDirection: 'column',
                                alignItems: 'center', zIndex: 10,
                            }}
                        >
                            {/* Marker dot */}
                            <div style={{
                                width: '4px', height: '4px', borderRadius: '50%',
                                background: 'white', boxShadow: '0 0 4px rgba(255,255,255,0.5)',
                            }} />
                            {/* Icon above */}
                            <div style={{
                                position: 'absolute', bottom: '12px',
                                fontSize: '0.7rem', opacity: 0.7,
                                transition: 'opacity 0.2s',
                            }}>
                                {getEventIcon(e.type || e.event_type)}
                            </div>
                        </div>
                    );
                })}

                {/* Playhead */}
                <div style={{
                    position: 'absolute', top: '50%', transform: 'translateY(-50%)',
                    left: `${progressPct}%`, width: '3px', height: '20px',
                    background: 'white', boxShadow: '0 0 10px rgba(255,255,255,0.6)',
                    borderRadius: '2px', transition: 'left 0.3s linear', zIndex: 20,
                }} />
            </div>

            {/* Lap labels */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
                <span style={{ fontSize: '0.55rem', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>L1</span>
                <span style={{ fontSize: '0.55rem', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>L{Math.floor(totalLaps / 2)}</span>
                <span style={{ fontSize: '0.55rem', fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)' }}>L{totalLaps}</span>
            </div>
        </div>
    );
};

export default RaceTimeline;
