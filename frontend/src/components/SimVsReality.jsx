
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


const ScoreBadge = ({ score }) => {
    let color = "text-red-500";
    let label = "POOR";
    let bg = "bg-red-500/20";

    if (score >= 75) {
        color = "text-green-500";
        label = "EXCELLENT";
        bg = "bg-green-500/20";
    } else if (score >= 50) {
        color = "text-yellow-500";
        label = "MODERATE";
        bg = "bg-yellow-500/20";
    }

    return (
        <div className={`flex items-center gap-2 px-3 py-1 rounded ${bg} border border-[color] ${color}`}>
            <span className="text-xl font-bold">{score?.toFixed(1)}</span>
            <div className="flex flex-col">
                <span className="text-xs font-bold tracking-wider">{label}</span>
                <span className="text-[10px] opacity-75">TARGET: &gt;75.0</span>
            </div>
        </div>
    );
};

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-gray-800 border border-gray-600 p-2 rounded shadow-xl">
                <p className="font-bold text-gray-200">Lap {label}</p>
                <p className="text-red-400">Delta: {payload[0].value.toFixed(3)}s</p>
            </div>
        );
    }
    return null;
};

const SimVsReality = () => {
    const [seasons] = useState([2024, 2023, 2022]);
    const [selectedSeason, setSelectedSeason] = useState(2024);
    const [availableRaces, setAvailableRaces] = useState([]);
    const [ingestedRaces, setIngestedRaces] = useState([]);
    const [ingesting, setIngesting] = useState(false);

    const [comparisonData, setComparisonData] = useState(null);
    const [loading, setLoading] = useState(false);

    // Fetch ingested races on mount
    useEffect(() => {
        fetchIngestedRaces();
    }, []);

    // Fetch available races when season changes
    useEffect(() => {
        fetch(`http://localhost:8000/api/reality/available/${selectedSeason}`)
            .then(res => res.json())
            .then(data => setAvailableRaces(data))
            .catch(err => console.error("Failed to fetch available races", err));
    }, [selectedSeason]);

    const fetchIngestedRaces = () => {
        fetch('http://localhost:8000/api/reality/races')
            .then(res => res.json())
            .then(data => setIngestedRaces(data))
            .catch(err => console.error("Failed to fetch ingested races", err));
    };

    const handleIngest = async (round, name, circuit) => {
        setIngesting(true);
        try {
            await fetch('http://localhost:8000/api/reality/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ season: selectedSeason, round })
            });
            alert(`Started ingestion for ${name}. This happens in background.`);
        } catch (err) {
            alert("Ingestion failed to start");
        } finally {
            setIngesting(false);
        }
    };

    const handleCompare = async (season, round) => {
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/api/reality/compare/${season}/${round}`);
            const data = await res.json();
            setComparisonData(data);
        } catch (err) {
            console.error("Comparison failed", err);
            alert("Failed to run comparison");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-6 text-white bg-gray-900 min-h-screen">
            <h1 className="text-3xl font-bold mb-6 text-red-600">Reality Injection & Calibration</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* LEFT: INGESTION */}
                <div className="panel bg-gray-800 p-4 rounded-lg">
                    <h2 className="text-xl font-bold mb-4">1. Ingest Real Data</h2>
                    <div className="flex gap-4 mb-4">
                        <select
                            value={selectedSeason}
                            onChange={e => setSelectedSeason(Number(e.target.value))}
                            className="bg-gray-700 p-2 rounded"
                        >
                            {seasons.map(s => <option key={s} value={s}>{s}</option>)}
                        </select>
                    </div>

                    <div className="h-64 overflow-y-auto border border-gray-700 rounded">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-gray-700 sticky top-0">
                                <tr>
                                    <th className="p-2">Round</th>
                                    <th className="p-2">Grand Prix</th>
                                    <th className="p-2">Circuit</th>
                                    <th className="p-2">Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {availableRaces.map(r => (
                                    <tr key={r.round_num} className="border-b border-gray-700 hover:bg-gray-750">
                                        <td className="p-2">{r.round_num}</td>
                                        <td className="p-2">{r.name}</td>
                                        <td className="p-2">{r.circuit}</td>
                                        <td className="p-2">
                                            <button
                                                onClick={() => handleIngest(r.round_num, r.name, r.circuit)}
                                                disabled={ingesting}
                                                className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs"
                                            >
                                                {ingesting ? '...' : 'Ingest'}
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* RIGHT: COMPARISON */}
                <div className="panel bg-gray-800 p-4 rounded-lg">
                    <h2 className="text-xl font-bold mb-4">2. Compare Simulation</h2>
                    <button onClick={fetchIngestedRaces} className="text-xs underline mb-2">Refresh List</button>

                    <div className="flex flex-wrap gap-2 mb-4">
                        {ingestedRaces.length === 0 && <p className="text-gray-400">No races ingested yet.</p>}
                        {ingestedRaces.map(r => (
                            <div key={`${r.season}-${r.round}`} className="bg-gray-700 p-3 rounded flex items-center justify-between gap-4">
                                <span>{r.season} Round {r.round}</span>
                                <button
                                    onClick={() => handleCompare(r.season, r.round)}
                                    disabled={loading}
                                    className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-xs"
                                >
                                    {loading ? 'Running Sim...' : 'Run Comparison'}
                                </button>
                            </div>
                        ))}
                    </div>

                    {comparisonData && (
                        <div className="bg-gray-900 p-4 rounded border border-gray-700">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-gray-400 text-sm upppercase">Calibration Score</h3>
                                    <ScoreBadge score={comparisonData.summary.score} />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                                <div className="p-3 bg-gray-800 rounded">
                                    <span className="text-gray-400 block mb-1">Pos Accuracy (Kendall)</span>
                                    <div className="font-mono text-lg font-bold">{comparisonData.summary.avg_position_accuracy?.toFixed(3)}</div>
                                    <span className="text-xs text-gray-500">1.0 = Perfect match</span>
                                </div>
                                <div className="p-3 bg-gray-800 rounded">
                                    <span className="text-gray-400 block mb-1">Lap Time Delta</span>
                                    <div className="font-mono text-lg font-bold">{comparisonData.summary.avg_lap_time_delta?.toFixed(3)}s</div>
                                    <span className="text-xs text-gray-500">Lower is better</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* BOTTOM: CHARTS */}
            {comparisonData && (
                <div className="mt-8 panel bg-gray-800 p-4 rounded-lg">
                    <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <span>Lap-by-Lap Analysis</span>
                        <span className="text-xs font-normal text-gray-400 bg-gray-700 px-2 py-1 rounded">Delta (Sim - Real)</span>
                    </h2>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={comparisonData.details.lap_time_delta.map((d, i) => ({ lap: i + 1, delta: d }))}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                                <XAxis dataKey="lap" stroke="#888" />
                                <YAxis stroke="#888" label={{ value: 'Delta (s)', angle: -90, position: 'insideLeft' }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="delta"
                                    stroke="#ec2222"
                                    strokeWidth={2}
                                    name="Lap Time Error"
                                    dot={{ r: 2, fill: '#ec2222' }}
                                    activeDot={{ r: 6 }}
                                />
                                {/* Zero reference line */}
                                <Line type="monotone" dataKey={() => 0} stroke="#4ade80" strokeDasharray="5 5" strokeWidth={1} name="Ideal Match" dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SimVsReality;
