import React from 'react';

const Home = ({ onNavigate }) => {
    return (
        <div className="home-container">
            {/* Header / Branding */}
            <div className="home-header">
                <div className="home-title-block">
                    <h1 className="home-main-title">BOX BOX</h1>
                    <p className="home-subtitle">INTELLIGENCE LABORATORY</p>
                </div>
            </div>

            {/* Split Screen Hero */}
            <div className="hero-split">

                {/* LEFT CARD: 2026 Predictions */}
                <div
                    className="hero-card card-predictions"
                    onClick={() => {
                        // For now we might just alert or navigate to a placeholder view
                        alert("2026 Predictions Simulation Module Loading... (Coming Soon!)")
                        // onNavigate('2026_predictions') 
                    }}
                >
                    <div className="hero-card-content">
                        <div className="hero-icon-wrapper">
                            <span className="hero-icon">🔮</span>
                        </div>
                        <h2 className="hero-card-title">2026 PREDICTIONS</h2>
                        <p className="hero-card-desc">
                            Run 100,000 Monte Carlo simulations on the upcoming season. Analyze regulation changes and performance shifts.
                        </p>
                        <div className="hero-card-footer">
                            <span className="hero-action-text">INITIALIZE MODEL →</span>
                        </div>
                    </div>
                    {/* Abstract techy background elements */}
                    <div className="cyber-grid"></div>
                    <div className="glow-orb blue-orb"></div>
                </div>

                {/* RIGHT CARD: Create Your Own Scenario */}
                <div
                    className="hero-card card-scenario"
                    onClick={() => onNavigate('scenarios')}
                >
                    <div className="hero-card-content">
                        <div className="hero-icon-wrapper">
                            <span className="hero-icon">🏎️</span>
                        </div>
                        <h2 className="hero-card-title">SCENARIO LABORATORY</h2>
                        <p className="hero-card-desc">
                            Construct race scenarios from scratch. Adjust engineering setups, weather timelines, driver personas, and chaos multipliers.
                        </p>
                        <div className="hero-card-footer">
                            <span className="hero-action-text">ENTER LABORATORY →</span>
                        </div>
                    </div>
                    <div className="cyber-grid"></div>
                    <div className="glow-orb red-orb"></div>
                </div>

            </div>
        </div>
    );
};

export default Home;
