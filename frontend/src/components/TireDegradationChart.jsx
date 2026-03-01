import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea } from 'recharts';

const TEAM_COLORS = {
    'VER': '#3671C6', 'HAM': '#6CD3BF', 'LEC': '#F91536', 'NOR': '#F58020',
    'ALO': '#358C75', 'SAI': '#F91536', 'RUS': '#6CD3BF', 'PIA': '#F58020',
    'PER': '#3671C6', 'GAS': '#2293D1', 'STR': '#358C75', 'HUL': '#B6BABD'
};

const COMPOUND_DEG_RATES = {
    SOFT: 0.045,
    MEDIUM: 0.028,
    HARD: 0.018,
    INTERMEDIATE: 0.035,
    WET: 0.022
};

const TireDegradationChart = ({ raceState, activeConfig }) => {
    if (!raceState?.cars || raceState.cars.length === 0) return null;

    const totalLaps = activeConfig?.race_structure?.total_laps || 50;
    const currentLap = activeConfig?.race_structure?.starting_lap || 0;
    const remainingLaps = totalLaps - currentLap;
    const projectionLaps = Math.min(remainingLaps, 30);

    // Build projection data for top 5 drivers
    const topDrivers = raceState.cars.slice(0, 5);

    const data = [];
    for (let lap = 0; lap <= projectionLaps; lap++) {
        const point = { lap: currentLap + lap };
        topDrivers.forEach(car => {
            const compound = car.tire_compound || 'MEDIUM';
            const baseRate = COMPOUND_DEG_RATES[compound] || 0.028;
            const currentWear = car.tire_wear || 0;
            const currentAge = car.tire_age || 0;

            // Logistic/sigmoid degradation curve: smooth acceleration near cliff
            // Models real tire behavior where deg accelerates gradually, not as a wall
            const effectiveAge = currentAge + lap;
            const cliffCenter = 28; // laps at which cliff midpoint occurs
            const cliffSteepness = 0.18; // how sharp the transition is
            const logisticMultiplier = 1.0 + 1.5 / (1.0 + Math.exp(-cliffSteepness * (effectiveAge - cliffCenter)));
            const projectedWear = Math.min(1.0, currentWear + (lap * baseRate * logisticMultiplier));

            point[car.driver] = Number((projectedWear * 100).toFixed(1));
        });
        data.push(point);
    }

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>Lap {label}</div>
                    {payload.map((entry, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '2px' }}>
                            <span style={{ fontSize: '0.75rem', color: entry.color, fontWeight: 700 }}>{entry.dataKey}</span>
                            <span style={{ fontSize: '0.75rem', color: '#ccc', fontFamily: 'var(--font-mono)' }}>{entry.value}%</span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '300px', flex: 1, borderTop: '2px solid #ef4444' }}>
            <h2 className="panel-title" style={{ marginBottom: '4px', color: '#ef4444' }}>TIRE DEGRADATION PROJECTION</h2>
            <div className="text-xs" style={{ color: '#888', marginBottom: '12px' }}>
                Projected wear curve over {projectionLaps} laps • <span style={{ color: '#ef4444' }}>Red zone = cliff danger (&gt;80%)</span>
            </div>
            <div style={{ flex: 1, minHeight: 0, width: '100%' }}>
                <ResponsiveContainer width="100%" height={240}>
                    <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                        <defs>
                            <linearGradient id="cliffZone" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#ef4444" stopOpacity={0.15} />
                                <stop offset="100%" stopColor="#ef4444" stopOpacity={0.02} />
                            </linearGradient>
                        </defs>
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
                            tickFormatter={(val) => `${val}%`}
                            domain={[0, 100]}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        {/* Cliff danger zone */}
                        <ReferenceArea y1={80} y2={100} fill="url(#cliffZone)" strokeOpacity={0} />
                        <ReferenceLine y={80} stroke="#ef4444" strokeDasharray="4 4" strokeOpacity={0.5} />
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

export default TireDegradationChart;
