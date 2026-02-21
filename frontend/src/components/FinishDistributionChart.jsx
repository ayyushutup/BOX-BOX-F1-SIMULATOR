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

const FinishDistributionChart = ({ predictions, selectedDriver }) => {
    if (!selectedDriver) return null;

    // Synthetic distribution data for a Bell-curve / Histogram effect
    // Real implementation would pull this from the Monte Carlo backend based on the slider state
    const data = [];
    const basePeak = selectedDriver.charCodeAt(0) % 10 + 2; // Arbitrary center for the bell curve

    for (let pos = 1; pos <= 20; pos++) {
        // Simple normal distribution function approximation for visuals
        const distance = Math.abs(pos - basePeak);
        let prob = 0;
        if (distance === 0) prob = 35;
        else if (distance === 1) prob = 20;
        else if (distance === 2) prob = 8;
        else if (distance === 3) prob = 3;
        else if (distance === 4) prob = 1;

        // Add some noise
        prob = prob > 0 ? prob + Math.random() * 2 : 0;

        data.push({
            position: `P${pos}`,
            probability: Number(prob.toFixed(1))
        });
    }

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #333', padding: '10px', borderRadius: '4px' }}>
                    <p style={{ margin: '0 0 5px 0', fontSize: '0.85rem', color: '#fff', fontWeight: 800 }}>{label} LIKELIHOOD</p>
                    <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        <span style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--cyan)' }}>
                            {payload[0].value}%
                        </span>
                    </div>
                </div>
            )
        }
        return null;
    }

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '300px', flex: 1, borderTop: '2px solid var(--purple)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 className="panel-title" style={{ marginBottom: 0, color: 'var(--purple)' }}>FINISH DISTRIBUTION SPREAD</h2>
                <div className="text-xs font-mono" style={{ color: 'var(--purple)' }}>DRIVER: {selectedDriver}</div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis
                            dataKey="position"
                            stroke="#555"
                            tick={{ fill: '#888', fontSize: 10, fontFamily: 'var(--font-mono)' }}
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
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />

                        <Bar dataKey="probability" radius={[2, 2, 0, 0]}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={TEAM_COLORS[selectedDriver] || 'var(--purple)'} fillOpacity={0.8} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default FinishDistributionChart;
