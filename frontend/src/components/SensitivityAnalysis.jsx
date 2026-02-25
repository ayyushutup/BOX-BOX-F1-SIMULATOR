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
        { variable: 'Weather', impact: 2.1 }, // positive means EV went up (e.g. 1st to 3rd = +2.0 = worse)
        { variable: 'SC Prob', impact: -1.2 }, // negative means EV went down (e.g. 5th to 4th = -1.0 = gain)
        { variable: 'Tire Deg.', impact: 0.8 },
        { variable: 'Aggression', impact: 0.4 },
        { variable: 'Track Temp', impact: 0.1 },
    ].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

    const getColor = (impact) => {
        if (impact >= 0.5) return 'var(--red)'; // Positive delta = worse position -> red
        if (impact <= -0.5) return 'var(--green)'; // Negative delta = better position -> green
        return '#888'; // Neural
    };

    const getExplanation = (impact) => {
        if (impact > 0) return `Worse by ${Math.abs(impact).toFixed(1)} positions`;
        if (impact < 0) return `Gain ${Math.abs(impact).toFixed(1)} positions`;
        return 'No effect';
    };

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                    <p style={{ margin: '0 0 5px 0', fontSize: '0.75rem', color: '#888', fontWeight: 700 }}>{data.variable.toUpperCase()} SENSITIVITY</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: getColor(data.impact) }}>
                            {data.impact > 0 ? '+' : ''}{data.impact.toFixed(1)} ΔP
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#ccc' }}>
                            {getExplanation(data.impact)}
                        </span>
                    </div>
                </div>
            )
        }
        return null;
    }

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '230px', flex: 1, borderTop: '2px solid #555' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                    <h2 className="panel-title" style={{ marginBottom: '4px', color: '#ccc' }}>SENSITIVITY HEATMAP</h2>
                    <div className="text-xs" style={{ color: '#888' }}>
                        Units: Impact on Expected Position (ΔP)
                    </div>
                </div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} layout="vertical" margin={{ top: 0, right: 30, left: 10, bottom: 0 }}>
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
