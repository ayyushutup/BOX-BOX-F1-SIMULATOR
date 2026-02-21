function Header() {
    return (
        <header className="header-bar">
            <h1 className="header">BOX BOX <span style={{ fontSize: '0.4em', color: 'var(--text-tertiary)', letterSpacing: '4px', marginLeft: '12px' }}>PREDICTION ENGINE</span></h1>
            <div className="header-stats">
                <div className="stat-box hero-stat">
                    <span className="stat-label">MODE</span>
                    <span className="stat-value" style={{ color: 'var(--red)' }}>SCENARIO LAB</span>
                </div>
            </div>
        </header>
    )
}

export default Header