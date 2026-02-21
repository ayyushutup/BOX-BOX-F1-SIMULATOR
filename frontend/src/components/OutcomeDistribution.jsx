import React from 'react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts'

const TEAM_COLORS = {
    'VER': '#3671C6',
    'HAM': '#6CD3BF',
    'LEC': '#F91536',
    'NOR': '#F58020',
    'ALO': '#358C75',
    'SAI': '#F91536',
    'RUS': '#6CD3BF',
    'PIA': '#F58020'
};

const OutcomeDistribution = ({ predictions, raceState }) => {
    // Generate static outcome distribution data
    // In a real scenario, this is the aggregated output of the Monte Carlo batch

    let data = [];
    if (predictions && predictions.win_prob) {
        data = Object.keys(predictions.win_prob).map(driver => ({
            driver,
            winProb: Math.round(predictions.win_prob[driver] * 100),
            podiumProb: predictions.podium_prob ? Math.round(predictions.podium_prob[driver] * 100) : 0,
        })).sort((a, b) => b.winProb - a.winProb).slice(0, 8); // Top 8
    } else {
        // Fallback / Demonstration data
        data = [
            { driver: 'VER', winProb: 45, podiumProb: 88 },
            { driver: 'NOR', winProb: 22, podiumProb: 75 },
            { driver: 'LEC', winProb: 15, podiumProb: 60 },
            { driver: 'HAM', winProb: 10, podiumProb: 45 },
            { driver: 'SAI', winProb: 5, podiumProb: 30 },
            { driver: 'RUS', winProb: 2, podiumProb: 20 },
            { driver: 'PIA', winProb: 1, podiumProb: 15 },
        ];
    }

    if (data.length === 0) return null;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #333', padding: '12px', borderRadius: '4px', minWidth: '150px' }}>
                    <p style={{ margin: '0 0 8px 0', fontSize: '1rem', color: TEAM_COLORS[label] || '#fff', fontWeight: 800 }}>{label}</p>
                    {payload.map((entry, index) => (
                        <div key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <span style={{ fontSize: '0.75rem', color: '#ccc' }}>{entry.name}</span>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: entry.fill }}>
                                {entry.value}%
                            </span>
                        </div>
                    ))}
                </div>
            )
        }
        return null;
    }

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '320px', flex: 1, borderTop: '2px solid var(--cyan)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 className="panel-title" style={{ marginBottom: 0, color: 'var(--cyan)' }}>FINAL OUTCOME DISTRIBUTION</h2>
                <div className="text-xs font-mono" style={{ color: 'var(--cyan)' }}>MONTE CARLO PROJECTION (n=5,000)</div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 30, left: -20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis
                            dataKey="driver"
                            stroke="#555"
                            tick={{ fill: '#fff', fontSize: 12, fontWeight: 700 }}
                            tickMargin={10}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="#555"
                            tick={{ fill: '#888', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(val) => `${val}%`}
                            axisLine={false}
                            tickLine={false}
                            domain={[0, 100]}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />

                        <Bar dataKey="podiumProb" name="PODIUM PROBABILITY" fill="#444" radius={[4, 4, 0, 0]} barSize={40} />
                        <Bar dataKey="winProb" name="WIN PROBABILITY" radius={[4, 4, 0, 0]} barSize={40}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={TEAM_COLORS[entry.driver] || 'var(--red)'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default OutcomeDistribution;
