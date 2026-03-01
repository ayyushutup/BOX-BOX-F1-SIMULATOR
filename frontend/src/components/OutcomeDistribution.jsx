import React, { useState } from 'react'
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

const OutcomeDistribution = ({ predictions, baselinePredictions, raceState }) => {
    const [compareMode, setCompareMode] = useState(true);

    let data = [];
    if (predictions && predictions.mc_win_distribution) {
        // Collect all top drivers from both baseline and current
        const allDrivers = new Set([
            ...Object.keys(predictions.mc_win_distribution || {}),
            ...Object.keys(baselinePredictions?.mc_win_distribution || {})
        ]);

        data = Array.from(allDrivers).map(driver => {
            const baseWin = baselinePredictions?.mc_win_distribution?.[driver] || 0;
            const modWin = predictions.mc_win_distribution?.[driver] || 0;
            const basePodium = baselinePredictions?.podium_prob?.[driver] || 0;
            const modPodium = predictions.podium_prob?.[driver] || 0;

            // Map car telemetry for hover drilldown
            const carContext = raceState?.cars?.find(c => c.driver === driver);

            // Delta for compare mode visualization
            const delta = Number(((modWin - baseWin) * 100).toFixed(1));

            return {
                driver,
                winProb: Number((modWin * 100).toFixed(1)),
                baselineWin: Number((baseWin * 100).toFixed(1)),
                podiumProb: Number((modPodium * 100).toFixed(1)),
                baselinePodium: Number((basePodium * 100).toFixed(1)),
                deltaWin: delta,
                deltaBar: delta, // Separate field for the delta bar
                tyreLife: carContext ? Math.round((1 - carContext.tire_wear) * 100) : '--',
                pitStops: carContext?.pit_stops ?? 0,
                interval: carContext?.interval ? `+${carContext.interval.toFixed(1)}s` : 'LEADER',
                causalFactors: predictions.causal_factors?.[driver] || []
            }
        }).sort((a, b) => b.winProb - a.winProb).slice(0, 10); // Top 10
    }

    if (data.length === 0) return null;

    // Get volatility bands for 95% CI display
    const topDriver = data[0]?.driver;
    const topBand = predictions?.volatility_bands?.[topDriver];
    const ciText = topBand ? `P${topBand.optimistic} – P${topBand.pessimistic}` : null;

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const driverData = payload[0].payload;
            const isComparing = compareMode && baselinePredictions;

            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '12px', borderRadius: '4px', minWidth: '200px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', borderBottom: '1px solid #333', paddingBottom: '4px' }}>
                        <span style={{ fontSize: '1.2rem', color: TEAM_COLORS[label] || '#fff', fontWeight: 800 }}>{label}</span>
                        {isComparing && (
                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: driverData.deltaWin > 0 ? 'var(--green)' : driverData.deltaWin < 0 ? 'var(--red)' : '#888' }}>
                                {driverData.deltaWin > 0 ? '+' : ''}{driverData.deltaWin}% Δ
                            </span>
                        )}
                    </div>

                    {/* Probabilities */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ fontSize: '0.75rem', color: '#aaa' }}>Win Prob:</span>
                            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#fff' }}>{driverData.winProb}%</span>
                        </div>
                        {isComparing && (
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: '0.75rem', color: '#666' }}>Base Win:</span>
                                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#888' }}>{driverData.baselineWin}%</span>
                            </div>
                        )}
                    </div>

                    {/* Causal Linkage / Context */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', borderTop: '1px dashed #333', paddingTop: '8px' }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--cyan)', letterSpacing: '1px' }}>CAUSAL CONTEXT</span>
                        {driverData.causalFactors && driverData.causalFactors.length > 0 ? (
                            <ul style={{ margin: '4px 0 0 16px', padding: 0, color: '#ccc', fontSize: '0.75rem', listStyleType: 'disc' }}>
                                {driverData.causalFactors.map((factor, idx) => (
                                    <li key={idx} style={{
                                        marginBottom: '3px',
                                        color: factor.includes('Penalty') || factor.includes('Warning') ? 'var(--red)' :
                                            factor.includes('Advantage') || factor.includes('Bonus') ? 'var(--green)' : '#ccc'
                                    }}>
                                        {factor}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#888' }}>Est. Tyre Life:</span>
                                    <span style={{ fontSize: '0.75rem', color: '#ccc' }}>{driverData.tyreLife}%</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#888' }}>Current Gap:</span>
                                    <span style={{ fontSize: '0.75rem', color: '#ccc' }}>{driverData.interval}</span>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#888' }}>Pit Stops:</span>
                                    <span style={{ fontSize: '0.75rem', color: '#ccc' }}>{driverData.pitStops}</span>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )
        }
        return null;
    }

    // Auto-scale Y-axis based on actual data
    const maxProb = Math.max(...data.map(d => Math.max(d.winProb, d.baselineWin || 0)));
    const yMax = Math.min(100, Math.ceil((maxProb + 10) / 10) * 10); // Round up to nearest 10
    const isComparing = compareMode && baselinePredictions !== null;

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '340px', flex: 1, borderTop: '2px solid var(--cyan)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                    <h2 className="panel-title" style={{ marginBottom: '4px', color: 'var(--cyan)' }}>FINAL OUTCOME DISTRIBUTION</h2>
                    <div className="text-xs" style={{ color: '#888' }}>
                        Expected Win: <span style={{ color: '#fff', fontWeight: 'bold' }}>{data[0]?.driver} ({data[0]?.winProb}%)</span> |
                        Volatility: <span style={{ color: 'var(--orange)' }}>{maxProb > 40 ? 'High' : maxProb > 25 ? 'Medium' : 'Low'}</span>
                        {ciText && (
                            <span style={{ marginLeft: '12px' }}>
                                80% CI: <span style={{ color: '#fff' }}>{ciText}</span>
                            </span>
                        )}
                    </div>
                </div>

                {/* Mode Toggle */}
                <div style={{ display: 'flex', background: 'rgba(0,0,0,0.5)', borderRadius: '4px', border: '1px solid #333', overflow: 'hidden' }}>
                    <button
                        onClick={() => setCompareMode(false)}
                        style={{ padding: '4px 8px', fontSize: '0.65rem', fontWeight: 700, border: 'none', background: !compareMode ? 'var(--cyan)' : 'transparent', color: !compareMode ? '#000' : '#888', cursor: 'pointer' }}
                    >
                        SNAPSHOT
                    </button>
                    <button
                        onClick={() => setCompareMode(true)}
                        style={{ padding: '4px 8px', fontSize: '0.65rem', fontWeight: 700, border: 'none', borderLeft: '1px solid #333', background: compareMode ? 'var(--cyan)' : 'transparent', color: compareMode ? '#000' : '#888', cursor: 'pointer' }}
                    >
                        COMPARE
                    </button>
                </div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 10, left: -20, bottom: 5 }} barGap={2}>
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
                            domain={[0, yMax]}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />

                        {isComparing ? (
                            <>
                                {/* Blue for Baseline */}
                                <Bar dataKey="baselineWin" name="BASELINE WIN" fill="#1C5B8A" radius={[2, 2, 0, 0]} animationDuration={800} />
                                {/* Orange/Team for Modified */}
                                <Bar dataKey="winProb" name="MODIFIED WIN" radius={[2, 2, 0, 0]} animationDuration={800}>
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={'#F58020'} />
                                    ))}
                                </Bar>
                            </>
                        ) : (
                            <>
                                <Bar dataKey="podiumProb" name="PODIUM PROBABILITY" fill="#444" radius={[4, 4, 0, 0]} barSize={40} animationDuration={800} />
                                <Bar dataKey="winProb" name="WIN PROBABILITY" radius={[4, 4, 0, 0]} barSize={40} animationDuration={800}>
                                    {data.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={TEAM_COLORS[entry.driver] || 'var(--red)'} />
                                    ))}
                                </Bar>
                            </>
                        )}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default OutcomeDistribution;
