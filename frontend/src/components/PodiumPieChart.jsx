import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const TEAM_COLORS = {
    'VER': '#3671C6', 'HAM': '#6CD3BF', 'LEC': '#F91536', 'NOR': '#F58020',
    'ALO': '#358C75', 'SAI': '#F91536', 'RUS': '#6CD3BF', 'PIA': '#F58020',
    'PER': '#3671C6', 'GAS': '#2293D1', 'OCO': '#2293D1', 'STR': '#358C75',
    'HUL': '#B6BABD', 'TSU': '#6692FF', 'RIC': '#6692FF', 'ALB': '#37BEDD',
    'BOT': '#C92D4B', 'MAG': '#B6BABD', 'ZHO': '#C92D4B', 'SAR': '#37BEDD'
};

const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
        const d = payload[0].payload;
        return (
            <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px 14px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                <div style={{ fontSize: '1.1rem', fontWeight: 800, color: TEAM_COLORS[d.driver] || '#fff', marginBottom: '4px' }}>{d.driver}</div>
                <div style={{ fontSize: '0.85rem', color: '#ccc' }}>Podium Chance: <span style={{ color: '#fff', fontWeight: 700 }}>{d.value.toFixed(1)}%</span></div>
            </div>
        );
    }
    return null;
};

const PodiumPieChart = ({ predictions }) => {
    if (!predictions?.podium_prob) return null;

    const data = Object.entries(predictions.podium_prob)
        .map(([driver, prob]) => ({ driver, value: prob * 100 }))
        .filter(d => d.value > 1)
        .sort((a, b) => b.value - a.value)
        .slice(0, 8);

    if (data.length === 0) return null;

    const topDriver = data[0];

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '280px', flex: 1, borderTop: '2px solid #f59e0b' }}>
            <h2 className="panel-title" style={{ marginBottom: '8px', color: '#f59e0b' }}>PODIUM PROBABILITY</h2>
            <div className="text-xs" style={{ color: '#888', marginBottom: '12px' }}>Top {data.length} drivers most likely to finish P1–P3</div>
            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={90}
                            paddingAngle={2}
                            dataKey="value"
                            animationBegin={100}
                            animationDuration={800}
                            stroke="rgba(0,0,0,0.3)"
                            strokeWidth={2}
                        >
                            {data.map((entry, i) => (
                                <Cell key={i} fill={TEAM_COLORS[entry.driver] || `hsl(${i * 45}, 60%, 50%)`} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                        {/* Center label */}
                        <text x="50%" y="46%" textAnchor="middle" dominantBaseline="central" style={{ fontSize: '1.4rem', fontWeight: 800, fill: TEAM_COLORS[topDriver.driver] || '#fff' }}>
                            {topDriver.driver}
                        </text>
                        <text x="50%" y="58%" textAnchor="middle" dominantBaseline="central" style={{ fontSize: '0.7rem', fill: '#888' }}>
                            {topDriver.value.toFixed(0)}% PODIUM
                        </text>
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default PodiumPieChart;
