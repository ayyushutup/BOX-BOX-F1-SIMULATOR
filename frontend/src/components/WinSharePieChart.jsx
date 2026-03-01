import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const TEAM_COLORS = {
    'VER': '#3671C6', 'HAM': '#6CD3BF', 'LEC': '#F91536', 'NOR': '#F58020',
    'ALO': '#358C75', 'SAI': '#F91536', 'RUS': '#6CD3BF', 'PIA': '#F58020',
    'PER': '#3671C6', 'GAS': '#2293D1', 'OCO': '#2293D1', 'STR': '#358C75',
    'HUL': '#B6BABD', 'TSU': '#6692FF', 'RIC': '#6692FF', 'ALB': '#37BEDD',
    'BOT': '#C92D4B', 'MAG': '#B6BABD', 'ZHO': '#C92D4B', 'SAR': '#37BEDD'
};

const RADIAN = Math.PI / 180;

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, driver }) => {
    if (percent < 0.04) return null;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
        <text x={x} y={y} fill="#fff" textAnchor="middle" dominantBaseline="central" style={{ fontSize: '0.7rem', fontWeight: 700, textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}>
            {driver}
        </text>
    );
};

const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
        const d = payload[0].payload;
        return (
            <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px 14px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: TEAM_COLORS[d.driver] || '#fff', marginBottom: '4px' }}>{d.driver}</div>
                <div style={{ fontSize: '0.85rem', color: '#ccc' }}>Win Share: <span style={{ color: '#fff', fontWeight: 700 }}>{d.value.toFixed(1)}%</span></div>
            </div>
        );
    }
    return null;
};

const WinSharePieChart = ({ predictions }) => {
    if (!predictions?.mc_win_distribution) return null;

    const data = Object.entries(predictions.mc_win_distribution)
        .map(([driver, prob]) => ({ driver, value: prob * 100 }))
        .filter(d => d.value > 0.5)
        .sort((a, b) => b.value - a.value)
        .slice(0, 10);

    if (data.length === 0) return null;

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '280px', flex: 1, borderTop: '2px solid #a855f7' }}>
            <h2 className="panel-title" style={{ marginBottom: '8px', color: '#a855f7' }}>WIN SHARE DISTRIBUTION</h2>
            <div className="text-xs" style={{ color: '#888', marginBottom: '12px' }}>Monte Carlo simulation win frequency across {Object.keys(predictions.mc_win_distribution).length} drivers</div>
            <div style={{ flex: 1, minHeight: 0, width: '100%' }}>
                <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={renderCustomLabel}
                            outerRadius={90}
                            dataKey="value"
                            animationBegin={0}
                            animationDuration={800}
                            stroke="rgba(0,0,0,0.3)"
                            strokeWidth={2}
                        >
                            {data.map((entry, i) => (
                                <Cell key={i} fill={TEAM_COLORS[entry.driver] || `hsl(${i * 36}, 70%, 50%)`} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default WinSharePieChart;
