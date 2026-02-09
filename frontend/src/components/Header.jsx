function Header({ lap, totalLaps, time }) {
    return (
        <header className="header-bar">
            <h1 className="header">BOX BOX</h1>
            <div className="header-stats">
                <div className="stat-box">
                    <span className="stat-label">STATUS</span>
                    <span className="stat-value">{lap === 0 ? 'GRID' : `LAP ${lap}/${totalLaps}`}</span>
                </div>
                <div className="stat-box">
                    <span className="stat-label">TIME</span>
                    <span className="stat-value">
                        {new Date(time).toISOString().slice(14, 23)}
                    </span>
                </div>
            </div>
        </header>
    )
}

export default Header