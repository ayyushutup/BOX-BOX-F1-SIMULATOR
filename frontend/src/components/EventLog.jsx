function EventLog({ events }) {
    // Show last 8 events
    const recentEvents = events.slice(-8).reverse()

    // Event type styling
    const getEventStyle = (type) => {
        switch (type) {
            case 'OVERTAKE':
                return { icon: '🏁', color: '#4CAF50' }
            case 'DNF':
                return { icon: '⚠️', color: '#FF5252' }
            case 'FASTEST_LAP':
                return { icon: '🟣', color: '#A855F7' }
            case 'SAFETY_CAR':
                return { icon: '🚗', color: '#FFC107' }
            case 'VIRTUAL_SAFETY_CAR':
                return { icon: '🟡', color: '#FFC107' }
            case 'PIT_STOP':
                return { icon: '🔧', color: '#2196F3' }
            case 'MODE_CHANGE':
                return { icon: '📻', color: '#00BCD4' }
            case 'YELLOW_FLAG':
                return { icon: '🟡', color: '#FFC107' }
            case 'GREEN_FLAG':
                return { icon: '🟢', color: '#4CAF50' }
            case 'RED_FLAG':
                return { icon: '🔴', color: '#FF1744' }
            default:
                return { icon: '📋', color: 'var(--text-dim)' }
        }
    }

    return (
        <div className="event-log-container">
            <div className="event-log-header">
                <span className="live-indicator">● LIVE</span>
                <span>RACE CONTROL MESSAGES</span>
            </div>
            <div className="event-log">
                {recentEvents.map((event, index) => {
                    const style = getEventStyle(event.type)
                    return (
                        <div
                            key={index}
                            className={`event-row ${index === 0 ? 'event-latest' : 'event-history'}`}
                        >
                            <span className="event-icon" style={{ color: style.color }}>{style.icon}</span>
                            <span className="event-lap">LAP {event.lap}</span>
                            <span className="event-text" style={{ color: index === 0 ? style.color : undefined }}>
                                {event.description}
                            </span>
                        </div>
                    )
                })}
                {events.length === 0 && (
                    <div className="event-row empty-log">
                        <span className="event-text">Monitoring track conditions...</span>
                    </div>
                )}
            </div>
        </div>
    )
}

export default EventLog
