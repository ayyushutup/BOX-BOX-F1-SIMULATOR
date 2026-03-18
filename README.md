# BOX BOX Simulator 🏎️🏁
*"Because 'Trust me bro' is not a valid pit wall strategy."*

Welcome to **BOX BOX**, the predictive F1 race simulation engine for strategy nerds, armchair team principals, and anyone who has ever yelled at their TV because Ferrari put Charles Leclerc on hard tires in the rain. 

Instead of guessing what might happen, BOX BOX simulates thousands of alternate realities (using actual math and Monte Carlo methods, not just good vibes) to predict exactly how a race will unfold under chaotic conditions.

## What Does It Do?
Box Box is a comprehensive full-stack ecosystem that generates probabilistic outcomes for F1 races. You feed it track data, driver aggression, chaotic events (like a random Latifi safety car), and weather modifiers. It then crunches the numbers and aggressively tells you who is mathematically favored to win, complete with expected value (EV) models for pit stops.

---

## Architecture & Workflow 🧠🔌

Box Box handles chaos using a beautifully layered architecture. Here is the workflow from your browser to the predictive models:

### 1. 🖥️ Frontend Command Center (React + Vite)
The UI acts as your glossy, glassmorphic command center.
- Captures your unhinged race scenarios (e.g., Max Verstappen on medium aggression, 80% rain chance at Spa).
- Displays interactive **Architecture Flowcharts**, live telemetry, and **Win Distribution Pies**.
- Powered by React, built with Vite, styled with a modern aesthetic that makes you feel like an actual race engineer.

### 2. 🔌 API Core (FastAPI)
The unyielding traffic cop of the system.
- Receives your scenario and checks if it makes sense (No, you can't race with 25 tires).
- Bridges the gap between the beautiful UI and the terrifying math happening in the background.
- Uses Python `asyncio` to simultaneously dispatch prediction tasks without blocking the pit lane.

### 3. 🏎️ Simulation Engine (Monte Carlo Run-Time)
This is where the multiverse happens.
- Runs parallel timeline forecasting using **Monte Carlo Simulation**.
- Tracks snowball effects like tyre degradation, fuel weight penalties, dirty air, and the infamous DRS trains.
- Simulates thousands of race variations to find the statistical truth of the current grid.

### 4. 🤖 ML & Physics Fusion (LightGBM + RL)
The brain inside the helmet.
- We don't just use physics; we use machine learning (LightGBM) trained on historical F1 telemetry.
- Custom Reinforcement Learning (RL) models predict the micro-battles at every corner.
- It calculates dynamic driver momentum and track grip changes as rubber gets laid down (or washed away).

### 5. 📊 Aggregated Outputs (The Results)
- The chaotic multiverse collapses back into a clean set of statistics.
- Sends probabilities, win confidence indices, and pit-stop Expected Value (EV) back to the UI.
- So you get receipts to show your friends why an undercut would have worked 85% of the time.

---

## Running the App Locally

*You don’t need an FIA Super License, just NPM and Python.*

```bash
# Start the entire grid (Frontend and Backend simultaneously)
bash run.sh
```

- **Frontend App**: `http://localhost:5173/`
- **Backend API**: `http://0.0.0.0:8000/`

*Note: If the prediction engine throws 404s, make sure you don't have zombie Python processes hogging your port 8000. We already killed them once, but they are persistent.*

---

## Contributing
Think you can improve our tyre degradation models? Found a bug where Alpine randomly wins every simulation? 

Feel free to open an issue or submit a pull request!
Just please, for the love of motorsport, write some tests before you break the Monte Carlo simulator.

<br/>
<p align="center">
  <i>Created by <a href="https://github.com/ayyushutup" target="_blank">Ayush R Thakur</a></i><br/>
  <i>No tires were harmed in the making of this software.</i>
</p>
