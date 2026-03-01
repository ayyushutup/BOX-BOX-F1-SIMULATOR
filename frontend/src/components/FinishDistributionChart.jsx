import React, { useState } from 'react'
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    ReferenceLine,
    ReferenceArea
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

const FinishDistributionChart = ({ predictions, baselinePredictions, selectedDriver }) => {
    const [compareMode, setCompareMode] = useState(true);

    if (!selectedDriver) return null;

    // Use backend distribution if available
    const data = [];
    const dist = predictions?.position_distributions?.[selectedDriver] || {};
    const baseDist = baselinePredictions?.position_distributions?.[selectedDriver] || {};

    // We want to graph P1 through P20 for a full curve
    let modEV = 0;
    let baseEV = 0;

    let cumulativeProb = 0;
    let p25 = 1, p75 = 20;
    let found25 = false, found75 = false;

    // Track mode (highest probability position)
    let modePos = 1;
    let modeProb = 0;

    // Track median
    let medianPos = 10;
    let foundMedian = false;

    const p10 = predictions?.volatility_bands?.[selectedDriver]?.optimistic;
    const p90 = predictions?.volatility_bands?.[selectedDriver]?.pessimistic;

    for (let pos = 1; pos <= 20; pos++) {
        const modProb = dist[pos] || 0;
        const baseProb = baseDist[pos] || 0;

        modEV += pos * modProb;
        baseEV += pos * baseProb;

        cumulativeProb += modProb;
        if (!found25 && cumulativeProb >= 0.25) { p25 = pos; found25 = true; }
        if (!foundMedian && cumulativeProb >= 0.50) { medianPos = pos; foundMedian = true; }
        if (!found75 && cumulativeProb >= 0.75) { p75 = pos; found75 = true; }

        // Track mode
        if (modProb > modeProb) { modeProb = modProb; modePos = pos; }

        // Full P1-P20 range — no cap
        data.push({
            position: `P${pos}`,
            posNum: pos,
            probability: Number((modProb * 100).toFixed(1)),
            baselineProb: Number((baseProb * 100).toFixed(1))
        });
    }

    // Fallback if no data
    if (modEV === 0 && baseEV === 0) {
        for (let pos = 1; pos <= 20; pos++) {
            const distance = Math.abs(pos - 3);
            let prob = distance === 0 ? 35 : distance === 1 ? 20 : distance === 2 ? 8 : 1;
            data.push({ position: `P${pos}`, posNum: pos, probability: prob, baselineProb: prob - (Math.random() * 2) });
        }
        modEV = 3.2; baseEV = 3.5; modePos = 3; medianPos = 3;
    }

    const isComparing = compareMode && baselinePredictions !== null;
    const deltaEV = modEV - baseEV; // negative is better (lower position)

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const point = payload[0].payload;
            return (
                <div style={{ background: 'rgba(10,12,18,0.95)', border: '1px solid #444', padding: '10px', borderRadius: '4px', boxShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
                    <p style={{ margin: '0 0 5px 0', fontSize: '1rem', color: '#fff', fontWeight: 800 }}>{label} PROBABILITY</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', minWidth: '120px' }}>
                            <span style={{ fontSize: '0.8rem', color: TEAM_COLORS[selectedDriver] || 'var(--purple)' }}>Modified:</span>
                            <span style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#fff' }}>
                                {point.probability}%
                            </span>
                        </div>
                        {isComparing && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', minWidth: '120px' }}>
                                <span style={{ fontSize: '0.8rem', color: '#1C5B8A' }}>Baseline:</span>
                                <span style={{ fontSize: '0.9rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#ccc' }}>
                                    {point.baselineProb}%
                                </span>
                            </div>
                        )}
                        {isComparing && (
                            <div style={{ marginTop: '4px', paddingTop: '4px', borderTop: '1px dashed #444', textAlign: 'right', fontSize: '0.75rem', color: (point.probability - point.baselineProb) > 0 ? 'var(--green)' : 'var(--red)' }}>
                                {((point.probability - point.baselineProb) > 0 ? '+' : '')}{(point.probability - point.baselineProb).toFixed(1)}% Δ
                            </div>
                        )}
                    </div>
                </div>
            )
        }
        return null;
    }

    return (
        <div className="chart-widget hover-elevate" style={{ minHeight: '340px', flex: 1, borderTop: `2px solid ${TEAM_COLORS[selectedDriver] || 'var(--purple)'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                    <h2 className="panel-title" style={{ marginBottom: '4px', color: TEAM_COLORS[selectedDriver] || 'var(--purple)' }}>FINISH DISTRIBUTION SPREAD</h2>
                    <div className="text-xs" style={{ color: '#888' }}>
                        Driver: <span style={{ color: '#fff', fontWeight: 'bold' }}>{selectedDriver}</span> |
                        Expected Pos: <span style={{ color: '#fff' }}>{modEV.toFixed(1)}</span>
                        {isComparing && deltaEV !== 0 && (
                            <span style={{ color: deltaEV < 0 ? 'var(--green)' : 'var(--red)', marginLeft: '6px' }}>
                                ({deltaEV < 0 ? '' : '+'}{deltaEV.toFixed(2)})
                            </span>
                        )}
                        <span style={{ marginLeft: '12px' }}>
                            Median: <span style={{ color: '#fff' }}>P{medianPos}</span>
                        </span>
                        <span style={{ marginLeft: '8px' }}>
                            Mode: <span style={{ color: 'var(--green)' }}>P{modePos}</span>
                        </span>
                        <span style={{ marginLeft: '12px' }}>
                            IQR: <span style={{ color: '#fff' }}>P{p25} - P{p75}</span>
                        </span>
                        {(p10 !== undefined && p90 !== undefined) && (
                            <span style={{ marginLeft: '12px', color: 'var(--orange)' }}>
                                80% CI: <span style={{ color: '#fff' }}>P{p10} - P{p90}</span>
                            </span>
                        )}
                    </div>
                </div>

                {/* Mode Toggle */}
                <div style={{ display: 'flex', background: 'rgba(0,0,0,0.5)', borderRadius: '4px', border: '1px solid #333', overflow: 'hidden' }}>
                    <button
                        onClick={() => setCompareMode(false)}
                        style={{ padding: '4px 8px', fontSize: '0.65rem', fontWeight: 700, border: 'none', background: !compareMode ? (TEAM_COLORS[selectedDriver] || 'var(--purple)') : 'transparent', color: !compareMode ? '#000' : '#888', cursor: 'pointer' }}
                    >
                        SNAPSHOT
                    </button>
                    <button
                        onClick={() => setCompareMode(true)}
                        style={{ padding: '4px 8px', fontSize: '0.65rem', fontWeight: 700, border: 'none', borderLeft: '1px solid #333', background: compareMode ? (TEAM_COLORS[selectedDriver] || 'var(--purple)') : 'transparent', color: compareMode ? '#000' : '#888', cursor: 'pointer' }}
                    >
                        COMPARE
                    </button>
                </div>
            </div>

            <div style={{ flex: 1, minHeight: 0, width: '100%', position: 'relative' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorModified" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={TEAM_COLORS[selectedDriver] || 'var(--purple)'} stopOpacity={0.8} />
                                <stop offset="95%" stopColor={TEAM_COLORS[selectedDriver] || 'var(--purple)'} stopOpacity={0.1} />
                            </linearGradient>
                            <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#1C5B8A" stopOpacity={0.5} />
                                <stop offset="95%" stopColor="#1C5B8A" stopOpacity={0.0} />
                            </linearGradient>
                        </defs>
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
                        <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.2)', strokeWidth: 1, strokeDasharray: '4 4' }} />

                        {/* Mid-50% Percentile Band Highlight */}
                        <ReferenceArea x1={`P${p25}`} x2={`P${p75}`} fill="rgba(255,255,255,0.03)" strokeOpacity={0} />
                        {(p10 !== undefined && p90 !== undefined) && (
                            <ReferenceArea x1={`P${p10}`} x2={`P${p90}`} fill="rgba(245, 128, 32, 0.05)" strokeOpacity={0} />
                        )}

                        {/* Median Line */}
                        <ReferenceLine x={`P${medianPos}`} stroke="#FFD700" strokeDasharray="5 3" label={{ position: 'top', value: 'MED', fill: '#FFD700', fontSize: 9, fontWeight: 700 }} />

                        {/* Mode Line */}
                        <ReferenceLine x={`P${modePos}`} stroke="var(--green)" strokeDasharray="2 2" label={{ position: 'insideTopRight', value: 'MODE', fill: 'var(--green)', fontSize: 9, fontWeight: 700 }} />

                        {isComparing && (
                            <ReferenceLine x={`P${Math.round(baseEV)}`} stroke="#1C5B8A" strokeDasharray="3 3" label={{ position: 'top', value: 'Base EV', fill: '#1C5B8A', fontSize: 10 }} />
                        )}
                        <ReferenceLine x={`P${Math.round(modEV)}`} stroke="#fff" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'EV', fill: '#fff', fontSize: 10 }} />

                        {isComparing && (
                            <Area type="monotone" dataKey="baselineProb" stroke="#1C5B8A" strokeWidth={2} fillOpacity={1} fill="url(#colorBaseline)" animationDuration={800} />
                        )}
                        <Area type="monotone" dataKey="probability" stroke={TEAM_COLORS[selectedDriver] || 'var(--purple)'} strokeWidth={3} fillOpacity={1} fill="url(#colorModified)" animationDuration={800} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    )
}

export default FinishDistributionChart;
