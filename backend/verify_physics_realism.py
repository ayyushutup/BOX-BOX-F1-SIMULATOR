
from app.simulation.data import create_race_state
from app.models.race_state import DrivingMode
from app.simulation.physics import calculate_dirty_air_penalty, calculate_speed

def verify_physics():
    print("Verifying Dirty Air & Strategy...")
    
    # Test 1: Dirty Air in SLOW sector
    gap = 0.5
    sector = "SLOW"
    penalty = calculate_dirty_air_penalty(gap, sector)
    print(f"Test 1 (Dirty Air): Gap={gap}s, Sector={sector} -> Penalty={penalty:.3f}")
    if penalty > 0.1:
        print("  ✅ PASS: Significant penalty applied")
    else:
        print("  ❌ FAIL: Penalty too low")

    # Test 2: Dirty Air in FAST sector (should be 0)
    gap = 0.5
    sector = "FAST"
    penalty_fast = calculate_dirty_air_penalty(gap, sector)
    print(f"Test 2 (Slipstream Zone): Gap={gap}s, Sector={sector} -> Penalty={penalty_fast:.3f}")
    if penalty_fast == 0.0:
        print("  ✅ PASS: No dirty air on straights")
    else:
        print("  ❌ FAIL: Penalty applied on straight")

    # Test 3: Driving Mode Speed
    base_speed = 200.0
    # Balanced
    s_bal = calculate_speed(base_speed, 0, 0, 0.9, rng=MockRNG(), driving_mode="BALANCED")
    # Push
    s_push = calculate_speed(base_speed, 0, 0, 0.9, rng=MockRNG(), driving_mode="PUSH")
    # Conserve
    s_cons = calculate_speed(base_speed, 0, 0, 0.9, rng=MockRNG(), driving_mode="CONSERVE")
    
    print(f"Test 3 (Modes): Base={base_speed}")
    print(f"  BALANCED: {s_bal:.1f}")
    print(f"  PUSH:     {s_push:.1f} (Should be higher)")
    print(f"  CONSERVE: {s_cons:.1f} (Should be lower)")
    
    if s_push > s_bal > s_cons:
        print("  ✅ PASS: Driving modes affect speed correctly")
    else:
        print("  ❌ FAIL: Speed hierarchy incorrect")

class MockRNG:
    def uniform(self, a, b): return 1.0 # No randomness

if __name__ == "__main__":
    verify_physics()
