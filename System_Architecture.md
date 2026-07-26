# Eco-Loop System Architecture

This document outlines the core architectural and strategic decisions implemented in the Eco-Loop AI-driven HVAC management system, specifically addressing the tool-calling framework, prompt engineering, latency management, and data handling.

## 1. Tool-Calling Architecture
Eco-Loop utilizes a local `Llama 3.1 (8B)` model integrated with **LangChain's Tool Calling** capabilities to achieve autonomous closed-loop control. The architecture completely decouples the cognitive layer from the physical simulation engine.

Instead of generating raw text that requires brittle regex parsing, the LLM is explicitly bound to deterministic Python functions via `@tool` decorators:
*   `get_building_state()`: Reads the current telemetry from `state.json`.
*   `set_hvac_setpoints(heating_setpoint, cooling_setpoint)`: Writes the physical actuation payload to `action.json`.

**The Control Loop**: The AI orchestrator (`agent.py`) runs in a continuous `while True` loop. In each iteration, it senses the environment (`state.json`), processes the thermal drift through a Chain-of-Thought, and invokes the `set_hvac_setpoints` tool natively. The EnergyPlus engine (`ep_runner.py`) actively polls `action.json` and adjusts the simulation parameters dynamically.

## 2. Prompt Engineering Strategies
The system prompt is designed to constrain the LLM to deterministic, physics-informed actions rather than conversational responses. 

**Key Strategies:**
*   **Role Constraint**: The prompt explicitly defines the agent as an "autonomous Eco-Loop Building Agent" focused strictly on energy minimization and thermal boundaries (21.0°C to 24.0°C).
*   **Predictive Heuristics**: The prompt injects explicit thermodynamic rules for predictive control. For example: *"Look at the Outdoor_Temp_C. If it's cold outside, use a lower heating setpoint. If it's hot outside, use a higher cooling setpoint."*
*   **Safety Guardrails**: Hard constraints are embedded in the prompt (e.g., *"CRITICAL RULE: Never let heating setpoint >= cooling setpoint"*) to prevent deadband fighting. This is double-checked by the tool function itself which rejects invalid arguments.
*   **Chain-of-Thought (CoT) Enforcement**: The prompt is designed to force the model to reason through the temperature drift before executing the tool. This reasoning is captured and streamed to the dashboard via `thoughts.txt` for user transparency.

## 3. Prompt Latency Management
To ensure the cognitive layer can keep pace with real-time building dynamics and avoid bottlenecking the simulation, latency is aggressively managed through several techniques:
*   **Edge Inference**: The entire cognitive stack runs locally using Ollama (`llama3.1`), entirely eliminating network round-trip latency associated with cloud APIs.
*   **Strict Temperature Control**: The LLM is initialized with `temperature=0.1`. This heavily limits the token search space, forcing the model to generate the most probable tokens faster and reducing token generation latency.
*   **Asynchronous Decoupling**: The Streamlit dashboard (`app.py`), the LLM agent (`agent.py`), and the simulation engine (`ep_runner.py`) run as completely separate background processes. The LLM's inference time never blocks the UI thread or the physics engine's execution loop.

## 4. Handling Lengthy Simulation Logs
EnergyPlus produces massive amounts of telemetry during an annual simulation run. Feeding these raw logs into an LLM would instantly exceed context windows and cause massive latency.

**Technical Approach:**
*   **State Condensation**: Instead of passing historical logs, the `ep_runner.py` acts as a data aggregator. It distills the complex building state down to a micro-payload (`state.json`) containing only the *current* crucial parameters (Current Time, Outdoor Temp, and the 5 Zone Temperatures). 
*   **Stateless Inference**: The LLM evaluates the state completely memorylessly. By only looking at the instantaneous thermal drift and outdoor conditions, the LLM context window remains incredibly small (a few hundred tokens).
*   **Out-of-Band Historical Storage**: While the LLM only sees instantaneous state, the full telemetry history is written in parallel to `ai_history.csv`. The Streamlit dashboard uses this CSV to render the long-term historical trajectory charts via Plotly, entirely bypassing the LLM.
