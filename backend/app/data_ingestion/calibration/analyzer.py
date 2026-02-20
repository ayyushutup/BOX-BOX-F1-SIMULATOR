"""
Calibration Analysis Tools.

Aggregates comparison results into human-readable reports and metrics.
"""

import numpy as np
from typing import Dict, Any

def summarize_calibration(comparison_results: Dict) -> Dict[str, Any]:
    """
    Generate summary statistics from raw comparison data.
    """
    pos_acc = comparison_results.get("position_accuracy", [])
    lap_delta = comparison_results.get("lap_time_delta", [])
    
    summary = {
        "laps_analyzed": comparison_results.get("laps_compared", 0),
        "metrics": {
            "avg_position_correlation": float(np.mean(pos_acc)) if pos_acc else 0.0,
            "min_position_correlation": float(np.min(pos_acc)) if pos_acc else 0.0,
            "avg_lap_time_error": float(np.mean(lap_delta)) if lap_delta else 0.0,
            "max_lap_time_error": float(np.max(lap_delta)) if lap_delta else 0.0,
        },
        "score": 0.0
    }
    
    # Simple score: 0-100 scale
    # Based on position correlation primarily
    tau = summary["metrics"]["avg_position_correlation"]
    score = max(0, tau) * 100
    summary["score"] = round(score, 1)
    
    return summary


def format_cli_report(summary: Dict) -> str:
    """Format summary as a text report."""
    m = summary["metrics"]
    return (
        f"CALIBRATION REPORT\n"
        f"------------------\n"
        f"Laps Analyzed: {summary['laps_analyzed']}\n"
        f"Overall Score: {summary['score']}/100\n\n"
        f"Position Correlation (Kendall Tau):\n"
        f"  Avg: {m['avg_position_correlation']:.3f}\n"
        f"  Min: {m['min_position_correlation']:.3f} (Worst Lap)\n\n"
        f"Lap Time Error:\n"
        f"  Avg: {m['avg_lap_time_error']:.3f}s\n"
        f"  Max: {m['max_lap_time_error']:.3f}s\n"
    )
