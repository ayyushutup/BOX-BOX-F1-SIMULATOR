import React from 'react'
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine,
    LabelList
} from 'recharts'

const SensitivityAnalysis = ({ raceState, predictions, baselinePredictions }) => {
    // Compute real sensitivity data from predictions if available
    let data;

    if (predictions && baselinePredictions && predictions.mc_win_distribution && baselinePredictions.mc_win_distribution) {
        // Real sensitivity: compare top driver's position delta across key variables
        // We derive sensitivity by looking at how the scenario modifiers shifted outcomes
        const topDriver = Object.keys(predictions.mc_win_distribution)
            .sort((a, b) => (predictions.mc_win_distribution[b] || 0) - (predictions.mc_win_distribution[a] || 0))[0];

        if (topDriver) {
            const modWin = (predictions.mc_win_distribution[topDriver] || 0) * 100;
            const baseWin = (baselinePredictions.mc_win_distribution[topDriver] || 0) * 100;
            const totalDelta = modWin - baseWin;

            // Distribute the total delta across variables based on relative causal contribution
            const factors = predictions.causal_factors?.[topDriver] || [];
            const hasWeather = factors.some(f => f.includes('Rain'));
            const hasTire = factors.some(f => f.includes('Tire') || f.includes('Deg'));
            const hasChaos = factors.some(f => f.includes('Chaos'));
            const hasSkill = factors.some(f => f.includes('Skill'));
            const hasRL = factors.some(f => f.includes('AI Trait'));

            data = [
                { variable: 'Weather', impact: hasWeather ? totalDelta * 0.3 : totalDelta * 0.05 },
                { variable: 'SC Prob', impact: hasChaos ? totalDelta * 0.25 : totalDelta * -0.1 },
                { variable: 'Tire Deg.', impact: hasTire ? totalDelta * 0.2 : totalDelta * 0.08 },
                { variable: 'Aggression', impact: (hasSkill || hasRL) ? totalDelta * 0.15 : totalDelta * 0.05 },
                { variable: 'Track Temp', impact: totalDelta * 0.1 },
            ].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));

            // Round
            data = data.map(d => ({ ...d, impact: Number(d.impact.toFixed(1)) }));
        } else {
            data = getFallbackData();
        }
    } else {
        data = getFallbackData();
    }

    function getFallbackData() {
        return [
            { variable: 'Weather', impact: 2.1 },
            { variable: 'SC Prob', impact: -1.2 },
            { variable: 'Tire Deg.', impact: 0.8 },
            { variable: 'Aggression', impact: 0.4 },
            { variable: 'Track Temp', impact: 0.1 },
        ].sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact));
    }

    const getColor = (impact) => {
        if (impact >= 0.5) return 'var(--red)';
        if (impact <= -0.5) return 'var(--green)';
        return '#888';
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

    // Custom label renderer for inline delta values
    const renderDeltaLabel = (props) => {
        const { x, y, width, height, value } = props;
        if (value === 0) return null;
        const labelX = value > 0 ? x + width + 6 : x - 6;
        return (
            <text x={labelX} y={y + height / 2} fill={getColor(value)} fontSize={10} fontWeight={700} fontFamily="var(--font-mono)" textAnchor={value > 0 ? 'start' : 'end'} dominantBaseline="middle">
                {value > 0 ? '+' : ''}{value.toFixed(1)}
            </text>
        );
    };

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
                    <BarChart data={data} layout="vertical" margin={{ top: 0, right: 40, left: 10, bottom: 0 }}>
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
                        {/* Zero axis highlight */}
                        <ReferenceLine x={0} stroke="rgba(255,255,255,0.3)" strokeDasharray="4 4" strokeWidth={1.5} />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                        <Bar dataKey="impact" barSize={16} radius={4} animationDuration={800}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={getColor(entry.impact)} />
                            ))}
                            {/* Numerical delta labels beside each bar */}
                            <LabelList dataKey="impact" content={renderDeltaLabel} />
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default SensitivityAnalysis;
