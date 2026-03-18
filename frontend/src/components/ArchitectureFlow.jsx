import React, { useState } from 'react';
import './ArchitectureFlow.css';

const NODES = {
    frontend: {
        id: 'frontend',
        icon: '🖥️',
        label: 'Frontend',
        title: 'React + Vite Interface',
        description: 'Scenario Lab, predictive panels, commentary, and distribution charts are rendered in a responsive React app built with Vite.',
        details: 'The UI acts as the command center. It captures user configurations (weather, driver aggression, track conditions) and streams real-time telemetry updates. The seamless experience is powered by React and Vite, using dynamic CSS for a glassmorphism aesthetic.',
        connections: ['api']
    },
    api: {
        id: 'api',
        icon: '🔌',
        label: 'API Core',
        title: 'FastAPI Service Layer',
        description: 'Scenario inputs are posted to FastAPI endpoints, which validate payloads and orchestrate prediction execution.',
        details: 'FastAPI serves as the highly concurrent backend bridge. It parses incoming prediction scenarios, coordinates data fetching from F1 caches, and instantly dispatches simulation tasks to the background engines using asyncio.',
        connections: ['simulation', 'ml']
    },
    simulation: {
        id: 'simulation',
        icon: '🏎️',
        label: 'Simulation Engine',
        title: 'Monte Carlo Race Simulator',
        description: 'Runs parallel timelines forecasting race volatility and generating thousands of possible finishing orders.',
        details: 'By running Monte Carlo simulations, the engine branches out into thousands of possible alternate reality races. It computes tire degradation, fuel weight penalties, and tracks the snowball effect of DRS trains and dirty air over time.',
        connections: ['output']
    },
    ml: {
        id: 'ml',
        icon: '🧠',
        label: 'ML Models',
        title: 'Physics + ML Fusion',
        description: 'Trained predictors combine with real-world race physics stochastic rules to estimate lap-by-lap outcomes.',
        details: 'LightGBM and custom reinforcement learning models evaluate driver momentum and track grip. The ML models do not just predict final positions; they predict the micro-battles at each corner, updating driver confidence indices dynamically.',
        connections: ['output']
    },
    output: {
        id: 'output',
        icon: '📊',
        label: 'Aggregated Outputs',
        title: 'Prediction Views',
        description: 'Results are aggregated into final standings, finish distribution spread, and comparative scenario analysis.',
        details: 'The massive dataset of simulated races is reduced into statistical confidence intervals. The output layer provides the frontend with precise win probabilities, expected value (EV) for pit stops, and podium likelihoods.',
        connections: []
    }
};

const ArchitectureFlow = () => {
    const [activeNodeId, setActiveNodeId] = useState('frontend');

    const handleNodeClick = (id) => {
        setActiveNodeId(id);
    };

    const activeNode = NODES[activeNodeId];

    // Helper to check if a connection path should be glowing
    const isPathActive = (from, to) => {
        if (activeNodeId === from || activeNodeId === to) return true;
        // Specific chains
        if (activeNodeId === 'frontend' && from === 'frontend') return true;
        if (activeNodeId === 'output' && to === 'output') return true;
        return false;
    };

    return (
        <div className="arch-flow-container">
            <div className="arch-flow-visual">
                {/* SVG for drawing animated connection lines */}
                <svg className="arch-flow-svg" viewBox="0 0 400 500" preserveAspectRatio="xMidYMid meet">
                    {/* Frontend to API */}
                    <path 
                        d="M 200,60 L 200,120" 
                        className={`arch-edge ${isPathActive('frontend', 'api') ? 'active-edge' : ''}`} 
                    />
                    
                    {/* API to Simulation and ML */}
                    <path 
                        d="M 200,180 L 200,210 L 100,210 L 100,250" 
                        className={`arch-edge ${isPathActive('api', 'simulation') ? 'active-edge' : ''}`} 
                    />
                    <path 
                        d="M 200,180 L 200,210 L 300,210 L 300,250" 
                        className={`arch-edge ${isPathActive('api', 'ml') ? 'active-edge' : ''}`} 
                    />

                    {/* Simulation and ML to Output */}
                    <path 
                        d="M 100,310 L 100,360 L 200,360 L 200,400" 
                        className={`arch-edge ${isPathActive('simulation', 'output') ? 'active-edge' : ''}`} 
                    />
                    <path 
                        d="M 300,310 L 300,360 L 200,360 L 200,400" 
                        className={`arch-edge ${isPathActive('ml', 'output') ? 'active-edge' : ''}`} 
                    />
                </svg>

                <div className="arch-grid">
                    {/* Top Row */}
                    <div className="arch-row row-top">
                        <button 
                            className={`arch-node ${activeNodeId === 'frontend' ? 'active' : ''}`}
                            onClick={() => handleNodeClick('frontend')}
                        >
                            <span className="node-icon">{NODES.frontend.icon}</span>
                            <span className="node-label">{NODES.frontend.label}</span>
                        </button>
                    </div>

                    {/* Middle Row */}
                    <div className="arch-row row-mid1">
                        <button 
                            className={`arch-node ${activeNodeId === 'api' ? 'active' : ''}`}
                            onClick={() => handleNodeClick('api')}
                        >
                            <span className="node-icon">{NODES.api.icon}</span>
                            <span className="node-label">{NODES.api.label}</span>
                        </button>
                    </div>

                    {/* Split Row */}
                    <div className="arch-row row-mid2 split">
                        <button 
                            className={`arch-node ${activeNodeId === 'simulation' ? 'active' : ''}`}
                            onClick={() => handleNodeClick('simulation')}
                        >
                            <span className="node-icon">{NODES.simulation.icon}</span>
                            <span className="node-label">{NODES.simulation.label}</span>
                        </button>
                        <button 
                            className={`arch-node ${activeNodeId === 'ml' ? 'active' : ''}`}
                            onClick={() => handleNodeClick('ml')}
                        >
                            <span className="node-icon">{NODES.ml.icon}</span>
                            <span className="node-label">{NODES.ml.label}</span>
                        </button>
                    </div>

                    {/* Bottom Row */}
                    <div className="arch-row row-bottom">
                        <button 
                            className={`arch-node ${activeNodeId === 'output' ? 'active' : ''}`}
                            onClick={() => handleNodeClick('output')}
                        >
                            <span className="node-icon">{NODES.output.icon}</span>
                            <span className="node-label">{NODES.output.label}</span>
                        </button>
                    </div>
                </div>
            </div>

            <div className="arch-flow-details">
                <div className="details-header">
                    <span className="details-icon">{activeNode.icon}</span>
                    <h3 className="details-title">{activeNode.title}</h3>
                </div>
                <div className="details-body">
                    <p className="details-summary">{activeNode.description}</p>
                    <div className="details-divider"></div>
                    <p className="details-extended">{activeNode.details}</p>
                </div>
            </div>
        </div>
    );
};

export default ArchitectureFlow;
