"""
CLI Race Runner - Watch a race simulation in the terminal.
Usage: python -m app.simulation.run_race --seed=42 --laps=10
"""

import argparse
from .data import create_race_state, TRACKS
from .engine import tick
from .rng import SeededRNG


def format_time(ms: int) -> str:
    """Convert milliseconds to MM:SS.mmm format."""
    minutes = ms // 60000
    seconds = (ms % 60000) // 1000
    millis = ms % 1000
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"


def print_standings(state, show_all: bool = False):
    """Print current race standings."""
    # Sort cars by position
    sorted_cars = sorted(state.cars, key=lambda c: c.position)
    
    print(f"\n{'='*60}")
    print(f"  LAP {sorted_cars[0].lap}/{state.meta.laps_total}  |  Time: {format_time(state.meta.timestamp)}")
    print(f"{'='*60}")
    print(f"  {'POS':<4} {'DRIVER':<6} {'TEAM':<20} {'TIRE':<6} {'LIFE':>6}")
    print(f"  {'-'*50}")
    
    cars_to_show = sorted_cars if show_all else sorted_cars[:10]
    
    for car in cars_to_show:
        tire = car.tire_state.compound.value[:3]  # First 3 letters
        # Show remaining tire life (100% = fresh, 0% = worn out)
        tire_life = (1.0 - car.tire_state.wear) * 100
        life_str = f"{tire_life:.1f}%"
        status = "" if car.status.value == "RACING" else f" [{car.status.value}]"
        print(f"  {car.position:<4} {car.driver:<6} {car.team:<20} {tire:<6} {life_str:>6}{status}")
    
    if not show_all and len(sorted_cars) > 10:
        print(f"  ... and {len(sorted_cars) - 10} more drivers")


def run_race(
    track_id: str = "monaco",
    seed: int = 42,
    laps: int = 10,
    show_every_lap: bool = True,
    show_all_drivers: bool = False
):
    """Run a full race simulation with CLI output."""
    
    print("\n" + "="*60)
    print("  BOX-BOX F1 SIMULATION ENGINE")
    print("="*60)
    print(f"  Track: {TRACKS[track_id].name}")
    print(f"  Laps:  {laps}")
    print(f"  Seed:  {seed}")
    print("="*60)
    
    # Create initial state
    state = create_race_state(track_id=track_id, seed=seed, laps=laps)
    rng = SeededRNG(seed)
    
    print("\n🏁 RACE START!")
    
    current_lap = 0
    ticks_per_lap_estimate = 600  # Rough estimate
    
    # Run simulation
    while not is_race_finished(state):
        state = tick(state, rng)
        
        # Check if leader completed a new lap
        leader = min(state.cars, key=lambda c: c.position)
        if leader.lap > current_lap:
            current_lap = leader.lap
            if show_every_lap:
                print_standings(state, show_all_drivers)
    
    # Final results
    print("\n" + "="*60)
    print("  🏁 RACE FINISHED! 🏁")
    print("="*60)
    print_final_results(state)
    
    return state


def is_race_finished(state) -> bool:
    """Check if the race is complete."""
    if not state.cars:
        return True
    leader = min(state.cars, key=lambda c: c.position)
    return leader.lap >= state.meta.laps_total


def print_final_results(state):
    """Print final race results."""
    sorted_cars = sorted(state.cars, key=lambda c: c.position)
    
    print(f"\n  {'POS':<4} {'DRIVER':<6} {'TEAM':<20} {'STOPS':<6} {'STATUS':<10}")
    print(f"  {'-'*50}")
    
    for car in sorted_cars:
        status = car.status.value
        print(f"  {car.position:<4} {car.driver:<6} {car.team:<20} {car.pit_stops:<6} {status:<10}")
    
    print(f"\n  Total simulation ticks: {state.meta.tick}")
    print(f"  Simulation time: {format_time(state.meta.timestamp)}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run a BOX-BOX F1 Race Simulation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for determinism")
    parser.add_argument("--laps", type=int, default=10, help="Number of laps")
    parser.add_argument("--track", type=str, default="monaco", choices=["monaco", "monza", "spa"])
    parser.add_argument("--all", action="store_true", help="Show all 20 drivers")
    parser.add_argument("--quiet", action="store_true", help="Only show final results")
    
    args = parser.parse_args()
    
    run_race(
        track_id=args.track,
        seed=args.seed,
        laps=args.laps,
        show_every_lap=not args.quiet,
        show_all_drivers=args.all
    )


if __name__ == "__main__":
    main()
