# Eco-Loop: Autonomous AI-Driven HVAC Management System

![Eco-Loop Dashboard Chart](assets/dashboard_chart.png)

Eco-Loop is a next-generation, closed-loop autonomous system designed to optimize enterprise-scale HVAC (Heating, Ventilation, and Air Conditioning) management. By replacing traditional, rigid PID controllers with an advanced cognitive architecture powered by Llama 3.1, Eco-Loop dynamically analyzes live thermal telemetry, anticipates environmental drift, and actively enforces optimal thermodynamic setpoints.

This architecture achieves significant energy reductions (**18.4% vs. baseline**) while strictly maintaining PMV (Predicted Mean Vote) comfort parameters across a global portfolio of buildings.

![Eco-Loop Dashboard Map](assets/dashboard_map.png)

## 🚀 Key Features

*   **Autonomous Edge AI**: Powered by a local Llama 3.1 (8B) model running entirely at the edge for zero-latency inference, extreme fault tolerance, and strict data privacy.
*   **Physics-Informed Actuation**: Uses EnergyPlus to model high-fidelity thermodynamic simulations of a complex, multi-zone commercial building distributed globally.
*   **Agentic Tool Calling**: The AI Orchestrator natively uses Tool Calling to invoke Python functions (e.g., `set_hvac_setpoints`) to actuate physical changes in the environment based on live data.
*   **Live Telemetry Dashboard**: A stunning, glassmorphic Streamlit Web UI featuring an interactive global map (powered by `streamlit-folium`), real-time charts (`plotly`), and live KPIs.
*   **Transparent AI Chain-of-Thought**: Exposes the raw cognitive reasoning of the Llama model, allowing human operators to see exactly *why* a specific HVAC decision was made.

## 🏗️ System Architecture

Eco-Loop operates on three fully decoupled, asynchronous core engines running concurrently, communicating via a rapid, zero-latency local Telemetry Bus.

1.  **Physics Engine (`ep_runner.py`)**: Runs EnergyPlus thermodynamic simulations.
2.  **AI Orchestrator (`agent.py`)**: Senses the state, evaluates thermal drift using Chain-of-Thought, and acts via Tool Calling.
3.  **Command & Control Dashboard (`app.py`)**: The interactive Streamlit frontend.

> For a complete architectural breakdown and data flow diagram, see the [System Architecture Document](System_Architecture.md).

## 🎥 PoC Demonstration Video
Watch the full Proof-of-Concept video demonstrating Eco-Loop in action—highlighting the live telemetry feed, real-time agentic tool-calling, and dynamic closed-loop control:
🔗 **[Watch on Google Drive](https://drive.google.com/file/d/11SZqyKlqgRkw0iyb9GH1mAXQGWcmlcXZ/view?usp=sharing)**

## 🛠️ Setup & Installation

### Prerequisites
*   Python 3.11+
*   [Ollama](https://ollama.com/) installed locally with the `llama3.1` model.

### Installation
1.  **Clone the repository**
    ```bash
    git clone https://github.com/aaryamanmodi353-rgb/Eco-Loop.git
    cd Eco-Loop
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ensure Ollama is running**
    ```bash
    ollama run llama3.1
    ```

## 💻 Usage

To launch the Eco-Loop platform, you need to run the three core engines concurrently. Open three separate terminal windows:

**Terminal 1: Start the Dashboard**
```bash
python -m streamlit run app.py
```

**Terminal 2: Start the Physics Simulation Engine**
```bash
python ep_runner.py
```

**Terminal 3: Start the AI Orchestrator**
```bash
python agent.py
```

Navigate to `http://localhost:8501` to view the live dashboard and interact with the global nodes.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

## 📜 License
This project is licensed under the MIT License.
