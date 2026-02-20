const ScenarioResults = ({ result, onBack, onReplay }) => {
    if (!result) return null

    const { final_positions, key_events, total_overtakes, total_pit_stops, dnfs, fastest_lap, strategy_summary } = result

    return (
        <div className="scenario-results-container">
            <div className="results-header">
                <button className="btn-back" onClick={onBack}>← SCENARIOS</button>
                <h1 className="results-title">{result.scenario_name}</h1>
                <button className="btn-replay" onClick={onReplay}>↻ REPLAY</button>
            </div>

            {/* Stats Bar */}
            <div className="results-stats-bar">
                <div className="result-stat">
                    <span className="result-stat-value">{total_overtakes}</span>
                    <span className="result-stat-label">OVERTAKES</span>
                </div>
                <div className="result-stat">
                    <span className="result-stat-value">{total_pit_stops}</span>
                    <span className="result-stat-label">PIT STOPS</span>
                </div>
                <div className="result-stat">
                    <span className="result-stat-value">{dnfs.length}</span>
                    <span className="result-stat-label">DNFs</span>
                </div>
                {fastest_lap && (
                    <div className="result-stat fastest-lap">
                        <span className="result-stat-value">{fastest_lap.driver} — {fastest_lap.time.toFixed(1)}s</span>
                        <span className="result-stat-label">⚡ FASTEST LAP</span>
                    </div>
                )}
            </div>

            {/* Final Classification */}
            <div className="results-classification">
                <h2 className="results-section-title">CLASSIFICATION</h2>
                <div className="classification-table">
                    <div className="table-header">
                        <span className="col-pos">POS</span>
                        <span className="col-driver">DRIVER</span>
                        <span className="col-team">TEAM</span>
                        <span className="col-gap">GAP</span>
                        <span className="col-best">BEST LAP</span>
                        <span className="col-tire">TIRE</span>
                        <span className="col-pits">PITS</span>
                        <span className="col-status">STATUS</span>
                    </div>
                    {final_positions.map((car, i) => (
                        <div key={car.driver} className={`table-row ${i < 3 ? 'podium' : ''} ${car.status === 'DNF' ? 'dnf' : ''}`}>
                            <span className="col-pos">
                                <span className={`pos-badge ${i === 0 ? 'p1' : i === 1 ? 'p2' : i === 2 ? 'p3' : ''}`}>
                                    P{car.position}
                                </span>
                            </span>
                            <span className="col-driver">{car.driver}</span>
                            <span className="col-team">{car.team}</span>
                            <span className="col-gap">
                                {car.position === 1 ? 'LEADER' : car.gap_to_leader ? `+${car.gap_to_leader.toFixed(1)}s` : '--'}
                            </span>
                            <span className="col-best">{car.best_lap_time ? `${car.best_lap_time.toFixed(1)}s` : '--'}</span>
                            <span className="col-tire">
                                <span className={`tire-dot ${car.tire_compound.toLowerCase()}`}></span>
                                {car.tire_compound}
                            </span>
                            <span className="col-pits">{car.pit_stops}</span>
                            <span className={`col-status ${car.status.toLowerCase()}`}>{car.status}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Strategy Summary */}
            {strategy_summary.length > 0 && (
                <div className="results-strategy">
                    <h2 className="results-section-title">STRATEGY BREAKDOWN</h2>
                    <div className="strategy-cards">
                        {strategy_summary.map(s => (
                            <div key={s.driver} className="strategy-card">
                                <div className="strategy-driver">{s.driver}</div>
                                <div className="strategy-detail">
                                    <span>P{s.start_position} → P{s.finish_position}</span>
                                    <span className={`positions-delta ${s.positions_gained > 0 ? 'gained' : s.positions_gained < 0 ? 'lost' : ''}`}>
                                        {s.positions_gained > 0 ? `+${s.positions_gained}` : s.positions_gained < 0 ? s.positions_gained : '='}
                                    </span>
                                </div>
                                <div className="strategy-tires">
                                    {s.compound_changes.length > 0
                                        ? s.compound_changes.map((c, i) => (
                                            <span key={i} className={`tire-chip ${c.toLowerCase()}`}>{c}</span>
                                        ))
                                        : <span className="tire-chip no-stop">NO STOP</span>
                                    }
                                    <span className="tire-arrow">→</span>
                                    <span className={`tire-chip ${s.final_tire.toLowerCase()}`}>{s.final_tire}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Key Events */}
            {key_events.length > 0 && (
                <div className="results-events">
                    <h2 className="results-section-title">KEY MOMENTS</h2>
                    <div className="events-timeline">
                        {key_events.slice(0, 20).map((evt, i) => (
                            <div key={i} className={`timeline-event ${evt.type.toLowerCase()}`}>
                                <span className="event-lap">LAP {evt.lap}</span>
                                <span className="event-desc">{evt.description}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default ScenarioResults
