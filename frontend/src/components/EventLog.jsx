function EventLog({ events }) {
    // Show last 4 events
    const recentEvents = events.slice(-4).reverse()

    return (
        <div className="event-log-container">
            <div className="event-log-header">
                <span className="live-indicator">● LIVE</span>
                <span>RACE CONTROL MESSAGES</span>
            </div>
            <div className="event-log">
                {recentEvents.map((event, index) => (
                    <div
                        key={index}
                        className={`event-row ${index === 0 ? 'event-latest' : 'event-history'}`}
                    >
                        <span className="event-lap">LAP {event.lap}</span>
                        <span className="event-text">{event.description}</span>
                    </div>
                ))}
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
