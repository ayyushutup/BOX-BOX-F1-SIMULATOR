import React, { useState, useEffect } from 'react';
import ArchitectureFlow from './ArchitectureFlow';
import car1 from '../assets/cars/ferrari_new.png';
import car2 from '../assets/cars/mclaren_new.png';
import car3 from '../assets/cars/mercedes_new.png';
import car4 from '../assets/cars/alpine_new.png';
import car5 from '../assets/cars/williams_new.png';
import car6 from '../assets/cars/redbull_new.png';
import car7 from '../assets/cars/audi_new.png';
import car8 from '../assets/cars/vcarb_new.png';

const TEAMS = [
    {
        id: 'ferrari',
        name: 'Ferrari',
        color: '#FF2800',
        carImage: car1,
        stats: {
            winProb: '38.7%',
            podiumChance: '71.0%',
            aggression: 'HIGH',
            chaosIndex: '0.64',
            safetyCarProb: '12%',
            lapTimeProjection: `1'21.4`
        }
    },
    {
        id: 'mclaren',
        name: 'McLaren',
        color: '#FF8700',
        carImage: car2,
        stats: {
            winProb: '25.3%',
            podiumChance: '65.5%',
            aggression: 'MEDIUM',
            chaosIndex: '0.55',
            safetyCarProb: '8%',
            lapTimeProjection: `1'21.8`
        }
    },
    {
        id: 'mercedes',
        name: 'Mercedes',
        color: '#00D2BE',
        carImage: car3,
        stats: {
            winProb: '18.1%',
            podiumChance: '45.0%',
            aggression: 'BALANCED',
            chaosIndex: '0.42',
            safetyCarProb: '5%',
            lapTimeProjection: `1'22.1`
        }
    },
    {
        id: 'alpine',
        name: 'Alpine',
        color: '#FD4BC7',
        carImage: car4,
        stats: {
            winProb: '3.4%',
            podiumChance: '12.0%',
            aggression: 'LOW',
            chaosIndex: '0.78',
            safetyCarProb: '18%',
            lapTimeProjection: `1'23.5`
        }
    },
    {
        id: 'williams',
        name: 'Williams',
        color: '#005AFF',
        carImage: car5,
        stats: {
            winProb: '0.5%',
            podiumChance: '2.5%',
            aggression: 'VARIABLE',
            chaosIndex: '0.91',
            safetyCarProb: '22%',
            lapTimeProjection: `1'24.0`
        }
    },
    {
        id: 'redbull',
        name: 'Red Bull',
        color: '#121F45', // Red Bull Navy
        carImage: car6,
        stats: {
            winProb: '28.4%',
            podiumChance: '60.1%',
            aggression: 'AGGRESSIVE',
            chaosIndex: '0.48',
            safetyCarProb: '10%',
            lapTimeProjection: `1'21.6`
        }
    },
    {
        id: 'audi',
        name: 'Audi',
        color: '#F50537', // Audi Sport Red
        carImage: car7,
        stats: {
            winProb: '2.1%',
            podiumChance: '8.5%',
            aggression: 'BALANCED',
            chaosIndex: '0.82',
            safetyCarProb: '15%',
            lapTimeProjection: `1'23.2`
        }
    },
    {
        id: 'vcarb',
        name: 'VCARB',
        color: '#1638f8', // VCARB Blue
        carImage: car8,
        stats: {
            winProb: '1.2%',
            podiumChance: '5.0%',
            aggression: 'HIGH',
            chaosIndex: '0.75',
            safetyCarProb: '14%',
            lapTimeProjection: `1'23.6`
        }
    }
];

const Home = ({ onNavigate }) => {
    const [activeTeamIndex, setActiveTeamIndex] = useState(0);
    const [autoPlay, setAutoPlay] = useState(true);
    const [activeInfoPanel, setActiveInfoPanel] = useState('what');

    useEffect(() => {
        let interval;
        if (autoPlay) {
            // User specifically asked for 0.5s updates, but 1000ms may be visually clearer if they want to read the text.
            // Using 500ms as requested!
            interval = setInterval(() => {
                setActiveTeamIndex((prev) => (prev + 1) % TEAMS.length);
            }, 500);
        }
        return () => clearInterval(interval);
    }, [autoPlay]);

    const activeTeam = TEAMS[activeTeamIndex];

    return (
        <div
            className="home-cinematic-container"
            style={{ '--accent-color': activeTeam.color }}
        >
            {/* Dynamic Background */}
            <div className="cinematic-bg">
                <div className="radial-glow"></div>
                <div className="telemetry-grid-bg"></div>
            </div>

            {/* Top Navigation */}
            <div className="cinematic-header">
                <div className="brand-logo">BOX BOX</div>
            </div>

            {/* Hero Section */}
            <div className="hero-cinematic">
                <div className="telemetry-overlay"></div>

                {/* Left Content */}
                <div className="hero-content">
                    <h1 className="hero-massive-title">
                        <span>SIMULATE</span>
                        <span>THE</span>
                        <span className="accent-text hero-title-accent" data-text="UNPREDICTABLE">UNPREDICTABLE</span>
                    </h1>
                    <p className="hero-description">
                        Configure race conditions, weather phases, and team modifiers.<br />
                        Run Monte Carlo predictions to compare standings, finish spread, and strategy impact.
                    </p>
                    <div className="hero-actions">
                        <button
                            className="btn-primary-action primary-btn"
                            onClick={() => onNavigate('scenarios')}
                        >
                            [ LAUNCH SIMULATION ]
                        </button>
                    </div>
                </div>

                {/* Right Visuals */}
                <div className="hero-visual">
                    <div className="car-showcase" onMouseEnter={() => setAutoPlay(false)} onMouseLeave={() => setAutoPlay(true)}>
                        <img
                            src={activeTeam.carImage}
                            alt={`${activeTeam.name} F1 Car`}
                            className="car-image parallax-car"
                        />
                        <div className="car-reflection"></div>
                    </div>
                </div>
            </div>

            <div className="home-info-section">
                <h2 className="home-info-heading">SYSTEM OVERVIEW</h2>
                <div className="home-info-actions">
                    <button
                        className={`home-info-button ${activeInfoPanel === 'what' ? 'active' : ''}`}
                        onClick={() => setActiveInfoPanel('what')}
                        type="button"
                    >
                        <span className="home-info-icon" aria-hidden="true">🏁</span>
                        <span>What is Box Box?</span>
                    </button>
                    <button
                        className={`home-info-button ${activeInfoPanel === 'how' ? 'active' : ''}`}
                        onClick={() => setActiveInfoPanel('how')}
                        type="button"
                    >
                        <span className="home-info-icon" aria-hidden="true">⚙️</span>
                        <span>How it Works</span>
                    </button>
                </div>

                {activeInfoPanel === 'what' ? (
                    <div className="home-info-panel">
                        <p>
                            Box Box is a race simulation lab for F1 fans, analysts, and strategy nerds who like to ask:
                            "What happens if this race turns chaotic on lap 23?"
                        </p>
                        <p>
                            You configure weather windows, race structure, and team/driver modifiers, then the engine
                            runs large Monte Carlo batches to project outcomes instead of guessing from one timeline.
                        </p>
                        <p>
                            The output is probability-first: projected final standings, finish position spread, and
                            strategy impact under different conditions. So it is less "trust me bro" and more
                            "here are 500 alternate universes and receipts."
                        </p>
                        <p>
                            Think of it as your virtual pit wall: slightly dramatic, highly opinionated, and usually
                            faster than waiting for real team radio to explain why Plan A became Plan Z.
                        </p>
                    </div>
                ) : (
                    <div className="home-info-panel" style={{ padding: 0, background: 'transparent', border: 'none', boxShadow: 'none' }}>
                        <ArchitectureFlow />
                    </div>
                )}
            </div>

            <footer className="home-page-footer">
                <div className="home-page-footer-grid">
                    <div className="home-footer-brand">
                        <div className="home-footer-logo">BOX BOX</div>
                        <p>Scenario-first F1 race simulation platform.</p>
                    </div>
                    <div className="home-footer-note">
                        <p>Built for race strategy testing, uncertainty modeling, and controlled chaos.</p>
                        <span>© {new Date().getFullYear()} BOX BOX Simulator</span>
                        <p style={{ marginTop: '8px', fontSize: '0.85rem' }}>
                            Created by <a href="https://github.com/ayyushutup" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--cyan)', textDecoration: 'none' }}>Ayush R Thakur</a>
                        </p>
                    </div>
                </div>
            </footer>

        </div>
    );
};

export default Home;
