import React, { useState, useEffect } from 'react';
import car1 from '../assets/cars/ferrari_new.png';
import car2 from '../assets/cars/mclaren_new.png';
import car3 from '../assets/cars/mercedes_new.png';
import car4 from '../assets/cars/alpine_new.png';
import car5 from '../assets/cars/williams_new.png';
import car6 from '../assets/cars/redbull_new.png';
import car7 from '../assets/cars/audi_new.png';
import car8 from '../assets/cars/vcarb_new.png';
import helmetBg from '../assets/vintage_helmet.jpg';

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

    // Scroll Reveal Effect
    useEffect(() => {
        const reveals = document.querySelectorAll('.reveal');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, { threshold: 0.2 });

        reveals.forEach(r => observer.observe(r));

        return () => {
            reveals.forEach(r => observer.unobserve(r));
        };
    }, []);

    const activeTeam = TEAMS[activeTeamIndex];

    const handleTeamSelect = (index) => {
        setActiveTeamIndex(index);
        setAutoPlay(false); // Stop auto-play when user interacts manually
    };

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
                        AI-powered 2026 Formula 1 race prediction engine.<br />
                        Real telemetry. Dynamic chaos modeling. Strategic probability shifts.
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

            {/* WHAT IS BOX BOX? - Explanation Section (Below Fold) */}
            <div className="platform-explanation">
                {/* Cinematic Background Visual Anchor */}
                <div className="explanation-visual-anchor"></div>

                <div className="explanation-content">
                    <h2 className="explanation-title heading-underline">
                        <span className="icon">🔬</span> WHAT IS BOX BOX?
                    </h2>

                    <p className="explanation-lead">
                        Box Box is a custom-built Formula 1 simulation engine that:
                    </p>

                    <div className="explanation-features-grid">
                        <div className="column-left reveal">
                            <div className="feature-item tech-card">
                                <div className="feature-icon">⚡</div>
                                <div className="feature-text">
                                    <strong>Stochastic Monte Carlo Engine</strong>
                                    By continuously running 100,000+ probabilistic race simulations per second, the engine maps out every possible timeline. It calculates real-time win probabilities, podium chances, and position distributions by dynamically modeling lap times, tire degradation curves, and individual driver consistencies instead of relying on static averages.
                                </div>
                            </div>
                            <div className="feature-item tech-card">
                                <div className="feature-icon">🌦</div>
                                <div className="feature-text">
                                    <strong>Dynamic Chaos & Volatility Modeling</strong>
                                    Racing isn't conducted in a vacuum. The engine actively models dynamic race chaos, injecting unpredictable variables like sudden Safety Cars, flash rain storms, and abrupt tire degradation cliffs. Our volatility index measures how mathematically sensitive current standings are to these chaotic events triggering.
                                </div>
                            </div>
                        </div>

                        <div className="column-right reveal">
                            <div className="feature-item tech-card">
                                <div className="feature-icon">🧠</div>
                                <div className="feature-text">
                                    <strong>Reinforcement Learning Strategy Agents</strong>
                                    Instead of hard-coded heuristics, Box Box utilizes active Reinforcement Learning (PPO) models to predict intelligent pit strategies. Each AI agent acts autonomously during the race, optimizing tire choices and push/save pacing based on unique driver personalities—weighing overtakes against tire preservation and risk tolerance.
                                </div>
                            </div>
                            <div className="feature-item tech-card">
                                <div className="feature-icon">📊</div>
                                <div className="feature-text">
                                    <strong>Causal Linkage & Telemetry Fusion</strong>
                                    Integrating real-world telemetry parameters with LightGBM foundational models, the system precisely understands why drivers perform differently. It doesn't just predict the outcome; it exposes the causal variables—such as dirty air penalty, fuel load, and compound transitions—driving the race's evolution.
                                </div>
                            </div>
                        </div>
                    </div>

                    <p className="explanation-footer">
                        Designed to model the upcoming 2026 regulations and test the limits of what AI can predict on the grid.
                    </p>
                </div>
            </div>

        </div>
    );
};

export default Home;
