# Eco-Loop Building Agents: System Architecture Document

## 1. Tool-Calling Architecture & Middleware

The system uses a highly decoupled **Co-Simulation Architecture** to prevent the LLM's inherently high-latency generation times from stalling the physics simulation engine. 

Instead of a traditional synchronous lock-step approach where EnergyPlus pauses indefinitely to wait for the LLM, we implemented an asynchronous **Shared State File-Bus (JSON)**:
*   **The Physics Engine (`ep_runner.py`):** Utilizes the official `pyenergyplus` API to hook into the `callback_begin_zone_timestep` runtime. At each timestep, it dumps the current building thermodynamics (Zone Mean Air Temperatures, Time, Day) into `state.json`. It immediately checks for `action.json`—if the AI has written a new setpoint, it injects it via Actuators. If not, it sleeps for a micro-delay and proceeds.
*   **The Cognitive Agent (`agent.py`):** Runs entirely independently using LangChain's Tool-Calling pipeline. It is provided with two deterministic tools: `get_building_state()` (reads `state.json`) and `set_hvac_setpoints()` (writes `action.json`).

This approach mimics a real-world BMS network where physical sensors and HVAC controllers operate on continuous sub-second loops, while supervisory AI controllers operate on slower, minutes-long horizons.

## 2. Prompt Engineering Strategies

The LLM is configured with a deterministic system prompt designed to ground its reasoning in building physics rather than arbitrary text generation.

*   **Role-Playing & Constraint Injection:** The prompt explicitly defines the agent's identity ("autonomous Eco-Loop Building Agent") and strictly defines its bounding box: *"Never let heating setpoint >= cooling setpoint"* to prevent deadband fighting (simultaneous heating and cooling).
*   **Chain-of-Thought (CoT) Enforcement:** The agent is instructed to *"always provide a brief reason for your action before calling the tool."* This forces the LLM to output its reasoning trace into the prompt scratchpad before emitting the JSON tool-call schema, significantly improving its logical accuracy when weighing comfort vs energy use.
*   **Supervisory Framing:** The prompt instructs the agent to relax setpoints when comfort is already achieved to actively save energy, acting as a forward-looking supervisor rather than a reactionary thermostat.

## 3. Prompt Latency Management

Standard Open-Source LLMs (like Llama 3 running locally via Ollama) introduce generation latencies ranging from 2 seconds to 30 seconds depending on hardware. In a continuous EnergyPlus simulation (which processes thousands of timesteps per second natively), this disparity causes massive desynchronization.

Our architecture manages this latency through **Asynchronous Polling**:
1.  The Agent is not triggered at every single EnergyPlus timestep (which would cause the simulation to take days). 
2.  Instead, the Agent runs in an infinite `while True` loop with a built-in `time.sleep(5)` delay. 
3.  Because the `pyenergyplus` runner constantly overwrites `state.json` with the *latest* data, the LLM always receives the most up-to-date state when it wakes up from its sleep cycle, effectively skipping thousands of intermediary timesteps while it was "thinking".

## 4. Handling Lengthy Simulation Logs

EnergyPlus natively outputs highly verbose CSV (`eplustbl.csv`), SQL, and standard text logs (`eplusout.eso`). Feeding these massive, multi-megabyte time-series logs directly into an LLM's context window would cause immediate context-overflow and tokenization limits to be breached.

Our technical approach mitigates this entirely:
*   **Selective Extraction:** We entirely bypass parsing the lengthy historic logs. Instead, we extract only the exact floating-point values needed *at runtime* (Zone Temperatures) directly from the C++ memory space using `api.exchange.get_variable_value()`.
*   **Context Window Protection:** The LLM's prompt context only ever contains the absolute current snapshot of the building (e.g., `{"SPACE1-1_Temp_C": 22.4, "hour": 14}`).
*   **Out-of-Band Analytics:** The historic time-series data is written out-of-band to a highly compressed `ai_history.csv` file by the Python bridge. This file is parsed exclusively by the Streamlit dashboard (`app.py`) for quantitative validation using Pandas, entirely shielding the LLM from lengthy data processing tasks it is poorly suited for.
