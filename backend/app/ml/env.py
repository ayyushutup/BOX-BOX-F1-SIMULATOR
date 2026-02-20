import numpy as np
import gymnasium as gym
from gymnasium import spaces
import math
from matplotlib.path import Path

from app.simulation.data import TRACKS
from app.simulation.physics import update_vehicle_dynamics

class F1RaceEnv(gym.Env):
    """
    OpenAI Gymnasium Environment for F1 Race Simulation (2D Kinematics).
    Allows an RL Agent to learn Throttle, Brake, and Steering inputs.
    """
    metadata = {"render_modes": ["human"], "render_fps": 10}

    def __init__(self, track_id="monza_synthetic", render_mode=None):
        super(F1RaceEnv, self).__init__()
        
        self.track = TRACKS.get(track_id)
        if not self.track.boundary:
            raise ValueError(f"Track {track_id} does not have a 2D boundary defined!")
            
        self.boundary = self.track.boundary
        
        # Build polygon paths for fast collision checking
        outer_poly = [(ox, oy) for ox, oy in zip(self.boundary.outer_x, self.boundary.outer_y)]
        inner_poly = [(ix, iy) for ix, iy in zip(self.boundary.inner_x, self.boundary.inner_y)]
        self.outer_path = Path(outer_poly)
        self.inner_path = Path(inner_poly)
        
        # ACTION SPACE: [steering, throttle, brake]
        # steering: -1.0 to 1.0 (Left/Right)
        # throttle: 0.0 to 1.0
        # brake: 0.0 to 1.0
        self.action_space = spaces.Box(
            low=np.array([-1.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0], dtype=np.float32),
            dtype=np.float32
        )
        
        # OBSERVATION SPACE (What the AI sees):
        # [speed_kmh, x, y, heading] + 5 LiDAR ray distances
        self.num_rays = 5
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(4 + self.num_rays,), dtype=np.float32
        )
        
        self.render_mode = render_mode
        self.reset()
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Start at (0, radius) for oval track (bottom straight)
        # We know inner_y[0] is the radius. Track width is 15, so subtract 7.5 to get center.
        start_y = self.boundary.inner_y[0] - 7.5 
        
        self.car_x = 0.0
        self.car_y = start_y
        self.car_heading = 0.0 # Facing right (+X)
        self.car_speed = 50.0 # Rolling start 50 km/h
        
        self.steps = 0
        self.max_steps = 2000 # 200 seconds of simulation
        self.total_reward = 0.0
        
        return self._get_obs(), {}
        
    def _get_obs(self):
        # Calculate simple rays to boundary
        rays = self._calculate_lidar_rays()
        obs = np.array([
            self.car_speed,
            self.car_x,
            self.car_y,
            self.car_heading,
        ] + rays, dtype=np.float32)
        return obs
        
    def _calculate_lidar_rays(self):
        # TODO: Implement precise raycasting intersections with self.outer_path
        # For now, return a naive fixed distance array to get the environment running.
        return [20.0, 20.0, 30.0, 20.0, 20.0]

    def step(self, action):
        self.steps += 1
        
        steering, throttle, brake = action
        
        # Update physics (dt = 0.1s, aligns with main simulation tick rate)
        self.car_x, self.car_y, self.car_heading, self.car_speed = update_vehicle_dynamics(
            x=self.car_x, y=self.car_y, heading=self.car_heading, speed_kmh=self.car_speed,
            throttle=throttle, brake=brake, steering=steering,
            grip_factor=1.0, dt_sec=0.1
        )
        
        obs = self._get_obs()
        
        # =========================
        # REWARD FUNCTION
        # =========================
        reward = 0.0
        terminated = False
        truncated = False
        
        # Reward 1: Forward Progress (Speed penalty for going backwards or too slow)
        reward += (self.car_speed / 100.0)
        
        # Reward 2: Penalty for heavy braking (simulating tire wear conservation)
        reward -= (brake * 0.05)
        
        # Collision Detection: Out of bounds
        if not self._is_on_track(self.car_x, self.car_y):
            reward -= 50.0  # Massive penalty for crashing
            terminated = True
            
        if self.steps >= self.max_steps:
            truncated = True
            
        self.total_reward += float(reward)
        return obs, float(reward), bool(terminated), bool(truncated), {}
        
    def _is_on_track(self, x, y):
        """Check if car is within the asphalt boundaries."""
        point = (x, y)
        
        # Must be INSIDE outer boundary, and OUTSIDE inner boundary
        if not self.outer_path.contains_point(point):
            return False
            
        # If it's inside the inner track (the grass infield), it's off track
        if self.inner_path.contains_point(point):
            return False
            
        return True
