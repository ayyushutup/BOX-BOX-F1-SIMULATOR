function Header({ lap, totalLaps, time }) {
    const formatTime = (ms) => {
        const totalSec = Math.floor(ms / 1000)
        const hrs = Math.floor(totalSec / 3600)
        const mins = Math.floor((totalSec % 3600) / 60)
        const secs = totalSec % 60
        const millis = Math.floor((ms % 1000) / 10)
        if (hrs > 0) return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(2, '0')}`
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(2, '0')}`
    }

    return (
        <header className="header-bar">
            <h1 className="header">BOX BOX</h1>
            <div className="header-stats">
                <div className="stat-box hero-stat">
                    <span className="stat-label">LAP</span>
                    <span className="stat-value">{lap === 0 ? 'GRID' : `${lap} / ${totalLaps}`}</span>
                </div>
                <div className="stat-box hero-stat">
                    <span className="stat-label">RACE TIME</span>
                    <span className="stat-value">{formatTime(time)}</span>
                </div>
            </div>
        </header>
    )
}

export default Header