import React, { useEffect, useState, useMemo } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const ConfidenceCurve = ({ isPlaying }) => {
    const [history, setHistory] = useState([]);

    useEffect(() => {
        let interval;
        const fetchData = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/ml/confidence-curve');
                if (res.ok) {
                    const data = await res.json();
                    if (data.snapshots) {
                        setHistory(data.snapshots);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch confidence curve", err);
            }
        };

        if (isPlaying) {
            fetchData();
            interval = setInterval(fetchData, 2000);
        } else {
            fetchData();
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [isPlaying]);

    const chartData = useMemo(() => {
        return history.map(snap => ({
            lap: snap.lap,
            tick: snap.tick,
            confidence: snap.confidence * 100
        }));
    }, [history]);

    if (!chartData || chartData.length === 0) {
        return null;
    }

    const currentConfidence = chartData[chartData.length - 1]?.confidence || 0;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: 'rgba(0,0,0,0.9)', border: '1px solid #333', padding: '6px 10px', fontSize: '10px', color: '#fff', borderRadius: '4px' }}>
                    <p style={{ margin: 0 }}>Lap: {label}</p>
                    <p style={{ margin: 0, color: '#00dc64', fontWeight: 700 }}>Confidence: {payload[0].value.toFixed(1)}%</p>
                </div>
            );
        }
        return null;
    };

    return (
        <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed #333' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', alignItems: 'center' }}>
                <span style={{ fontSize: '0.65rem', color: '#888', letterSpacing: '0.05em' }}>CONFIDENCE TREND</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div style={{
                        width: '8px', height: '8px', borderRadius: '50%',
                        background: currentConfidence > 70 ? '#00dc64' : currentConfidence > 40 ? '#ffc800' : '#ff4444',
                        boxShadow: `0 0 6px ${currentConfidence > 70 ? 'rgba(0,220,100,0.5)' : currentConfidence > 40 ? 'rgba(255,200,0,0.5)' : 'rgba(255,68,68,0.5)'}`,
                        animation: 'pulse-dot 2s ease-in-out infinite',
                    }} />
                    <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 700, color: currentConfidence > 70 ? '#00dc64' : currentConfidence > 40 ? '#ffc800' : '#ff4444' }}>
                        {currentConfidence.toFixed(0)}%
                    </span>
                </div>
            </div>
            <div style={{ width: '100%', height: '100px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                        <defs>
                            <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#00dc64" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#00dc64" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <XAxis
                            dataKey="lap" stroke="#444" fontSize={9}
                            tickLine={false} axisLine={{ stroke: '#333' }} minTickGap={15}
                        />
                        <YAxis
                            domain={[0, 100]} stroke="#444" fontSize={9}
                            tickLine={false} axisLine={false}
                            tickFormatter={(val) => `${val}%`}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <ReferenceLine y={80} stroke="rgba(0, 220, 100, 0.2)" strokeDasharray="3 3" />
                        <Area
                            type="monotone" dataKey="confidence"
                            stroke="#00dc64" strokeWidth={2}
                            fill="url(#confGrad)"
                            dot={false} isAnimationActive={false}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <style>{`
                @keyframes pulse-dot {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.6; transform: scale(1.3); }
                }
            `}</style>
        </div>
    );
};

export default ConfidenceCurve;
