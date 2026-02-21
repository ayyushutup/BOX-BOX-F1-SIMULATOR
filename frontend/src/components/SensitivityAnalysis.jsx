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

const SensitivityAnalysis = ({ raceState }) => {
    // Generate synthetic sensitivity data.
    // Represents which variables are moving the championship/race outcome EV the most
    const data = [
        { variable: 'Tire Deg.', impact: 0.8, type: 'positive' },
        { variable: 'SC Prob', impact: -1.2, type: 'negative' },
        { variable: 'Aggression', impact: 0.4, type: 'positive' },
        { variable: 'Weather', impact: 2.1, type: 'highly-volatile' },
        { variable: 'Track Temp', impact: 0.1, type: 'neutral' },
    ].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

    const getColor = (impact) => {
        const abs = Math.abs(impact);
        if (abs > 1.5) return 'var(--purple)';
        if (impact > 0.5) return 'var(--green)';
        if (impact < -0.5) return 'var(--red)';
        return '#888';
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #333', padding: '10px', borderRadius: '4px' }}>
                    <p style={{ margin: '0 0 5px 0', fontSize: '0.75rem', color: '#888', fontWeight: 700 }}>{data.variable.toUpperCase()} IMPACT</p>
                    <span style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: getColor(data.impact) }}>
                        {data.impact > 0 ? '+' : ''}{data.impact} EV SHIFT
                    </span>
                </div>
            )
        }
        return null;
    }

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '220px', flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 className="panel-title" style={{ marginBottom: 0 }}>SENSITIVITY HEATMAP</h2>
                <div className="text-xs font-mono text-gray-500">POS. IMPACT VARIANCE</div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: 10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={true} vertical={false} />
                        <XAxis
                            type="number"
                            stroke="#555"
                            tick={{ fill: '#888', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            domain={[-3, 3]}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            dataKey="variable"
                            type="category"
                            stroke="#555"
                            tick={{ fill: '#ccc', fontSize: 10, fontWeight: 600 }}
                            axisLine={false}
                            tickLine={false}
                            width={80}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                        <Bar dataKey="impact" barSize={16} radius={4}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getColor(entry.impact)} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default SensitivityAnalysis;
