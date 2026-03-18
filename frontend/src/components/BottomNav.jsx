import React from 'react';

const BottomNav = ({ activeSection, onSectionChange }) => {
    const navItems = [
        { id: 'scenario', label: 'LAB', icon: '🧪' }
    ];

    return (
        <nav className="bottom-nav mobile-only">
            {navItems.map(item => (
                <button
                    key={item.id}
                    className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
                    onClick={() => onSectionChange(item.id)}
                >
                    <span className="nav-icon">{item.icon}</span>
                    <span className="nav-label">{item.label}</span>
                </button>
            ))}

            <style>{`
                .bottom-nav {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 70px;
                    background: rgba(10, 11, 14, 0.95);
                    backdrop-filter: blur(20px);
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    display: flex;
                    justify-content: space-around;
                    align-items: center;
                    padding: 0 10px;
                    z-index: 1000;
                    box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.5);
                }
                .nav-item {
                    background: transparent;
                    border: none;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 4px;
                    color: var(--text-tertiary);
                    cursor: pointer;
                    transition: all 0.2s ease;
                    flex: 1;
                    padding: 8px 0;
                }
                .nav-item.active {
                    color: var(--red);
                }
                .nav-icon {
                    font-size: 1.2rem;
                }
                .nav-label {
                    font-size: 0.6rem;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                }
                .nav-item.active .nav-icon {
                    transform: translateY(-2px);
                    filter: drop-shadow(0 0 5px var(--red-glow));
                }
            `}</style>
        </nav>
    );
};

export default BottomNav;
