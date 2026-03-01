import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const TEAM_COLORS = {
    'VER': '#3671C6', 'HAM': '#6CD3BF', 'LEC': '#F91536', 'NOR': '#F58020',
    'ALO': '#358C75', 'SAI': '#F91536', 'RUS': '#6CD3BF', 'PIA': '#F58020',
    'PER': '#3671C6', 'GAS': '#2293D1', 'STR': '#358C75', 'HUL': '#B6BABD'
};

const LapTimeComparisonChart = ({ raceState, predictions }) => {
    if (!raceState?.cars || raceState.cars.length === 0) return null;

    // Sort by position
    const sortedCars = [...raceState.cars].sort((a, b) => a.position - b.position);
    const topDrivers = sortedCars.slice(0, 6);
    const leader = topDrivers[0];

    // Generate simulated lap time deltas over 15 laps
    // Based on skill, tire age, and gap
    const projectionLaps = 15;
    const data = [];

    for (let lap = 1; lap <= projectionLaps; lap++) {
        const point = { lap };
        topDrivers.forEach(car => {
            const skill = 0.90; // baseline
            const winProb = predictions?.mc_win_distribution?.[car.driver] || 0.05;

            // Base gap delta (lower position = higher delta initially)
            const baseDelta = car.position === 1 ? 0 : (car.interval || car.position * 0.8);

            // Tire effect: older tires increase gap over time
            const tireAge = (car.tire_age || 0) + lap;
            const tirePenalty = tireAge > 20 ? (tireAge - 20) * 0.06 : 0;

            // Faster drivers (higher win prob) close the gap gradually
            const convergenceFactor = winProb * lap * 0.15;

            const delta = Math.max(0, baseDelta + tirePenalty - convergenceFactor);
            point[car.driver] = Number(delta.toFixed(2));
        });
        data.push(point);
    }

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Lap {label}</div>
                    {payload.sort((a, b) => a.value - b.value).map((entry, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '2px' }}>
                            <span style={{ fontSize: '0.75rem', color: entry.color, fontWeight: 700 }}>{entry.dataKey}</span>
                            <span style={{ fontSize: '0.75rem', color: '#ccc', fontFamily: 'var(--font-mono)' }}>
                                {entry.value === 0 ? 'LEADER' : `+${entry.value}s`}
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '300px', flex: 1, borderTop: '2px solid #22d3ee' }}>
            <h2 className="panel-title" style={{ marginBottom: '4px', color: '#22d3ee' }}>LAP TIME GAP PROJECTION</h2>
            <div className="text-xs" style={{ color: '#888', marginBottom: '12px' }}>
                Projected gap to leader over {projectionLaps} laps • Based on tire deg, skill & MC probability
            </div>
            <div style={{ flex: 1, minHeight: 0, width: '100%' }}>
                <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis
                            dataKey="lap"
                            stroke="#555"
                            tick={{ fill: '#888', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(val) => `L${val}`}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="#555"
                            tick={{ fill: '#888', fontSize: 10, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(val) => `+${val}s`}
                            axisLine={false}
                            tickLine={false}
                            reversed={false}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" strokeDasharray="3 3" />
                        {topDrivers.map((car) => (
                            <Line
                                key={car.driver}
                                type="monotone"
                                dataKey={car.driver}
                                stroke={TEAM_COLORS[car.driver] || '#888'}
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 0 }}
                            />
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default LapTimeComparisonChart;
