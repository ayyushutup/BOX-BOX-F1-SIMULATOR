"""
Maps FastF1 circuit identifiers to our synthetic Track objects.

FastF1 uses CircuitShortName / CircuitKey, we need to match those
to the 4 tracks we have in data.py.
"""

from ..simulation.data import TRACKS

# FastF1 CircuitShortName -> our track ID
# Checked against fastf1.get_event_schedule() output
_CIRCUIT_NAME_MAP = {
    # Exact matches from FastF1's CircuitShortName column
    "Monaco":       "monaco",
    "Monza":        "monza",
    "Spa":          "spa",          # Spa-Francorchamps
    "Silverstone":  "silverstone",
    # Common alternate names / lowercase variants
    "monaco":       "monaco",
    "monza":        "monza",
    "spa":          "spa",
    "silverstone":  "silverstone",
    "Spa-Francorchamps": "spa",
}

# The set of circuits we actually support
SUPPORTED_CIRCUITS = set(TRACKS.keys())


def get_track_for_circuit(circuit_name: str):
    """
    Look up our synthetic Track for a FastF1 circuit name.
    """
    track_key = _CIRCUIT_NAME_MAP.get(circuit_name)
    
    if track_key is None:
        raise ValueError(
            f"Circuit '{circuit_name}' is not supported. "
            f"Supported circuits: {list(SUPPORTED_CIRCUITS)}"
        )
    
    # keys in TRACKS are "monaco", "monza" etc.
    # checking data.py again...
    # TRACKS = { "monaco": TRACK_MONACO, ... } 
    # BUT TRACK_MONACO.id is "monaco_synthetic"
    
    # So TRACKS["monaco"] returns an object with id="monaco_synthetic".
    # My test checks .id property.
    
    return TRACKS[track_key]


def is_supported_circuit(circuit_name: str) -> bool:
    """Check if we can map this circuit to one of our synthetic tracks."""
    return circuit_name in _CIRCUIT_NAME_MAP
