import React, { useState } from 'react';

const RaceCommentary = ({ commentary, reasoningTree, mode = 'standard', intensity = 'cinematic_high', onModeChange, onIntensityChange, disabled }) => {

    const [showReasoning, setShowReasoning] = useState(false);

    // Split into paragraphs if commentary exists
    const paragraphs = commentary ? commentary.split('\n\n').filter(p => p.trim()) : [];

    // Render text with inline markdown (bold, italic)
    const renderMarkdown = (text) => {
        const segments = [];
        let remaining = text;
        let key = 0;

        while (remaining.length > 0) {
            const boldIdx = remaining.indexOf('**');
            if (boldIdx !== -1) {
                const endBold = remaining.indexOf('**', boldIdx + 2);
                if (endBold !== -1) {
                    if (boldIdx > 0) {
                        segments.push(<span key={key++}>{remaining.slice(0, boldIdx)}</span>);
                    }
                    segments.push(
                        <strong key={key++} style={{ color: '#fff', fontWeight: 700 }}>
                            {remaining.slice(boldIdx + 2, endBold)}
                        </strong>
                    );
                    remaining = remaining.slice(endBold + 2);
                    continue;
                }
            }

            const italicMatch = remaining.match(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/);
            if (italicMatch) {
                const idx = remaining.indexOf(italicMatch[0]);
                if (idx > 0) {
                    segments.push(<span key={key++}>{remaining.slice(0, idx)}</span>);
                }
                segments.push(
                    <em key={key++} style={{ color: '#a0a0a0', fontStyle: 'italic' }}>
                        {italicMatch[1]}
                    </em>
                );
                remaining = remaining.slice(idx + italicMatch[0].length);
                continue;
            }

            segments.push(<span key={key++}>{remaining}</span>);
            break;
        }

        return segments;
    };

    // Confidence meter color
    const getConfColor = (score) => {
        if (score >= 70) return '#00dc64';
        if (score >= 40) return '#ffc800';
        return '#ff4444';
    };

    const confScore = reasoningTree?.confidence_score || 0;
    const confColor = getConfColor(confScore);

    return (
        <div
            style={{
                background: 'linear-gradient(135deg, rgba(12,12,18,0.97) 0%, rgba(30,22,8,0.92) 100%)',
                border: '1px solid rgba(245,158,11,0.2)',
                borderTop: '3px solid #f59e0b',
                borderRadius: '8px',
                padding: '20px 24px',
                position: 'relative',
                overflow: 'hidden',
            }}
        >
            {/* Ambient glow */}
            <div style={{
                position: 'absolute', top: -60, right: -60, width: 180, height: 180,
                borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(245,158,11,0.06) 0%, transparent 70%)',
                pointerEvents: 'none'
            }} />

            {/* Header with Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.4rem' }}>🎙️</span>
                    <h2 style={{
                        margin: 0, fontSize: '0.85rem', fontWeight: 800,
                        letterSpacing: '2px', color: '#f59e0b',
                        fontFamily: "'Inter', monospace"
                    }}>
                        RACE COMMENTARY
                    </h2>
                    <span style={{
                        fontSize: '0.5rem', color: '#999',
                        background: 'rgba(245,158,11,0.1)',
                        border: '1px solid rgba(245,158,11,0.25)',
                        padding: '3px 8px', borderRadius: '4px',
                        letterSpacing: '1.5px', fontWeight: 700
                    }}>
                        AI ANALYSIS
                    </span>

                    {/* Race Phase Badge */}
                    {reasoningTree?.race_phase && (
                        <span style={{
                            fontSize: '0.5rem',
                            color: reasoningTree.race_phase === 'late' ? '#ff4444' : reasoningTree.race_phase === 'mid' ? '#ffc800' : '#00dc64',
                            background: 'rgba(0,0,0,0.3)',
                            border: `1px solid ${reasoningTree.race_phase === 'late' ? 'rgba(255,68,68,0.3)' : reasoningTree.race_phase === 'mid' ? 'rgba(255,200,0,0.3)' : 'rgba(0,220,100,0.3)'}`,
                            padding: '3px 8px', borderRadius: '4px',
                            letterSpacing: '1.5px', fontWeight: 700, textTransform: 'uppercase'
                        }}>
                            {reasoningTree.race_phase} PHASE
                        </span>
                    )}

                    {/* Confidence Meter */}
                    {reasoningTree && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '8px' }}>
                            <div style={{ width: '60px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px', overflow: 'hidden' }}>
                                <div style={{
                                    width: `${confScore}%`, height: '100%',
                                    background: confColor,
                                    borderRadius: '3px',
                                    transition: 'width 0.5s ease',
                                    boxShadow: `0 0 6px ${confColor}40`
                                }} />
                            </div>
                            <span style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: confColor }}>
                                {confScore}%
                            </span>
                        </div>
                    )}
                </div>

                {/* Commentary Mode & Tone Controls */}
                <div style={{ display: 'flex', gap: '8px', zIndex: 10 }}>
                    <select
                        value={mode}
                        onChange={e => onModeChange && onModeChange(e.target.value)}
                        disabled={disabled}
                        style={{
                            background: 'rgba(0,0,0,0.5)', color: '#fff', border: '1px solid #333',
                            borderRadius: '4px', padding: '4px 8px', fontSize: '0.7rem', outline: 'none',
                            cursor: disabled ? 'not-allowed' : 'pointer'
                        }}
                    >
                        <option value="standard">Analyst Mode</option>
                        <option value="cinematic">Cinematic Mode</option>
                    </select>

                    {mode === 'cinematic' && (
                        <select
                            value={intensity}
                            onChange={e => onIntensityChange && onIntensityChange(e.target.value)}
                            disabled={disabled}
                            style={{
                                background: 'rgba(0,0,0,0.5)', color: '#fff', border: '1px solid #333',
                                borderRadius: '4px', padding: '4px 8px', fontSize: '0.7rem', outline: 'none',
                                cursor: disabled ? 'not-allowed' : 'pointer'
                            }}
                        >
                            <option value="cinematic_high">High Drama</option>
                            <option value="cinematic_low">Low Drama</option>
                            <option value="documentary">Documentary</option>
                            <option value="technical">Technical</option>
                        </select>
                    )}
                </div>
            </div>

            {/* Bias Warning Chips */}
            {reasoningTree?.bias_warnings?.length > 0 && (
                <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', flexWrap: 'wrap' }}>
                    {reasoningTree.bias_warnings.map((w, i) => (
                        <span key={i} style={{
                            fontSize: '0.6rem', fontWeight: 700,
                            color: '#f59e0b', background: 'rgba(245,158,11,0.1)',
                            border: '1px solid rgba(245,158,11,0.3)',
                            padding: '3px 10px', borderRadius: '12px',
                            letterSpacing: '0.5px'
                        }}>
                            ⚠️ {w}
                        </span>
                    ))}
                </div>
            )}

            {/* Commentary paragraphs */}
            <div style={{
                display: 'flex', flexDirection: 'column', gap: '12px',
                fontSize: '0.82rem', lineHeight: 1.7, color: '#ccc',
                fontFamily: "'Inter', -apple-system, sans-serif",
            }}>
                {!commentary ? (
                    <div style={{ color: '#888', fontStyle: 'italic', fontSize: '0.8rem' }}>
                        Awaiting data...
                    </div>
                ) : (
                    paragraphs.map((para, i) => (
                        <div
                            key={i}
                            style={{
                                padding: i === 0 ? '10px 14px' : '2px 0',
                                background: i === 0 ? 'rgba(245,158,11,0.05)' : 'transparent',
                                borderRadius: i === 0 ? '6px' : '0',
                                borderLeft: i === 0 ? '3px solid rgba(245,158,11,0.5)' : 'none',
                                fontSize: i === 0 ? '0.9rem' : '0.8rem',
                            }}
                        >
                            {renderMarkdown(para)}
                        </div>
                    ))
                )}
            </div>

            {/* Expandable Reasoning Tree */}
            {reasoningTree && reasoningTree.factors?.length > 0 && (
                <div style={{ marginTop: '16px', borderTop: '1px dashed rgba(245,158,11,0.2)', paddingTop: '12px' }}>
                    <button
                        onClick={() => setShowReasoning(!showReasoning)}
                        style={{
                            background: 'none', border: 'none', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: '8px',
                            color: '#888', fontSize: '0.7rem', fontWeight: 700,
                            letterSpacing: '1px', padding: 0
                        }}
                    >
                        <span style={{
                            display: 'inline-block',
                            transform: showReasoning ? 'rotate(90deg)' : 'rotate(0deg)',
                            transition: 'transform 0.2s',
                            fontSize: '0.8rem'
                        }}>▶</span>
                        REASONING TREE ({reasoningTree.factors.length} factors)
                    </button>

                    {showReasoning && (
                        <div style={{
                            marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px',
                            animation: 'fadeIn 0.3s ease'
                        }}>
                            {/* Headline */}
                            <div style={{
                                fontSize: '0.75rem', fontWeight: 700, color: '#f59e0b',
                                marginBottom: '4px', fontFamily: 'var(--font-mono)'
                            }}>
                                {reasoningTree.headline}
                            </div>

                            {/* Factor rows */}
                            {reasoningTree.factors.map((f, i) => {
                                const dirColor = f.direction === 'positive' ? '#00dc64' : f.direction === 'negative' ? '#ff4444' : '#888';
                                const dirIcon = f.direction === 'positive' ? '↑' : f.direction === 'negative' ? '↓' : '→';
                                const impactDots = f.impact === 'high' ? '●●●' : f.impact === 'medium' ? '●●○' : '●○○';

                                return (
                                    <div key={i} style={{
                                        display: 'flex', alignItems: 'center', gap: '10px',
                                        padding: '6px 10px', borderRadius: '4px',
                                        background: 'rgba(0,0,0,0.2)',
                                        borderLeft: `3px solid ${dirColor}`
                                    }}>
                                        <span style={{ fontSize: '0.85rem', color: dirColor, fontWeight: 700, width: '16px' }}>{dirIcon}</span>
                                        <span style={{ flex: 1, fontSize: '0.72rem', color: '#ccc' }}>{f.factor}</span>
                                        <span style={{ fontSize: '0.6rem', color: dirColor, fontFamily: 'var(--font-mono)', letterSpacing: '2px' }}>{impactDots}</span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            <style>{`
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-4px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default RaceCommentary;
