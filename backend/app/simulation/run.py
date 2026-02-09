"""
CLI runner for headless race simulation.
Usage: python -m app.simulation.run --seed=42 --laps=53 --track=monaco
"""

import argparse
from .data import create_race_state
from .engine import tick
from .rng import SeededRNG


def main():
    parser = argparse.ArgumentParser(description="Run F1 race simulation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    parser.add_argument("--laps", type=int, default=53, help="Total laps")
    parser.add_argument("--track", type=str, default="monaco", choices=["monaco", "monza", "spa", "silverstone"])
    args = parser.parse_args()
    
    print(f"\n🏎️  Box-Box F1 Simulation")
    print(f"   Track: {args.track.upper()}")
    print(f"   Laps: {args.laps}")
    print(f"   Seed: {args.seed}")
    print("=" * 50)
    
    state = create_race_state(
        track_id=args.track,
        seed=args.seed,
        laps=args.laps
    )
    rng = SeededRNG(args.seed)
    
    current_lap = 0
    tick_count = 0
    
    while True:
        state = tick(state, rng)
        tick_count += 1
        
        # Print lap updates when leader completes a lap
        leader = next((c for c in state.cars if c.position == 1), state.cars[0])
        
        if leader.lap > current_lap:
            current_lap = leader.lap
            print_lap_summary(state, current_lap)
            
            # Print any new events from this lap
            for event in state.events:
                if event.lap == current_lap:
                    print(f"    └─ {event.description}")
        
        # Check race finished
        if leader.lap >= args.laps:
            print_final_results(state)
            print(f"\n📊 Simulation completed in {tick_count} ticks")
            break


def print_lap_summary(state, lap):
    """Print summary of current lap."""
    racing_cars = [c for c in state.cars if c.status.value == "RACING"]
    top5 = sorted(racing_cars, key=lambda c: c.position)[:5]
    
    drivers = " | ".join([f"{c.driver} P{c.position}" for c in top5])
    
    # Add race condition indicators
    flags = ""
    if state.safety_car_active:
        flags += " 🚗 SC"
    if state.vsc_active:
        flags += " 🟡 VSC"
    
    print(f"Lap {lap:3d}: {drivers}{flags}")


def print_final_results(state):
    """Print final race results."""
    print("\n" + "=" * 50)
    print("🏁 RACE FINISHED")
    print("=" * 50)
    
    sorted_cars = sorted(state.cars, key=lambda c: (c.status.value != "RACING", c.position))
    
    for car in sorted_cars:
        if car.status.value == "RACING":
            icon = "🏆" if car.position <= 3 else "🏁"
            print(f"  {car.position:2d}. {car.driver} ({car.team}) {icon}")
        else:
            print(f"  -- {car.driver} ({car.team}) ❌ DNF")
    
    # Find fastest lap
    racing_cars = [c for c in state.cars if c.best_lap_time is not None]
    if racing_cars:
        fastest = min(racing_cars, key=lambda c: c.best_lap_time)
        minutes = int(fastest.best_lap_time // 60)
        seconds = fastest.best_lap_time % 60
        print(f"\n⏱️  Fastest Lap: {fastest.driver} - {minutes}:{seconds:06.3f}")


if __name__ == "__main__":
    main()
