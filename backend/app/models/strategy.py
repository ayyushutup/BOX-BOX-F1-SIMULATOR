from pydantic import BaseModel

class PitStrategyResult(BaseModel):
    should_pit: bool
    ev_score: float
    undercut_viable: bool
    drop_pos: float # or int, float is safer representing traffic flow index
    ideal_lap: int
