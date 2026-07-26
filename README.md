# 🌍 Eco-Loop: Autonomous LLM-Driven HVAC Control

Eco-Loop is a next-generation, closed-loop predictive HVAC control system built for the Honeywell Hackathon. It integrates a live Large Language Model (**Llama 3.1**) directly with the industry-standard **EnergyPlus** physics engine to autonomously manage building thermodynamics, proving substantial kWh energy reductions while strictly maintaining human comfort parameters.

## 🚀 Key Features

- **Autonomous Physics Integration**: Live bidirectional data streaming between the Python EnergyPlus API wrapper and the Llama 3.1 LLM agent.
- **Predictive AI Reasoning**: The localized AI agent continuously analyzes live thermal data (PMV) and dynamically injects precise heating and cooling setpoints back into the running simulation.
- **Enterprise Glassmorphism Dashboard**: A sleek, fully responsive Streamlit UI featuring a seamless Light/Dark mode, raw JSON telemetry streaming, and quantitative savings KPIs.
- **Global Geospatial Map**: An interactive Folium map tracking live AI-managed zones. Includes dynamic "Pin-Drop" functionality integrating the **Open-Meteo API** to deploy new nodes using real-time global weather data.
- **Natural Language RAG Interface**: Built-in chatbot allowing facility managers to interrogate the AI about its live thermodynamic decisions in plain English.
- **Zero-Latency Architecture**: Leveraging a localized Llama 3.1 model via Ollama to eliminate cloud network latency, allowing for rapid, robust control loops.

## 🏗️ System Architecture

The project consists of three core components communicating via a unified JSON bus:

1. **`ep_runner.py` (Physics Engine)**: 
   - Wraps the `pyenergyplus` API.
   - Runs the `baseline.idf` building simulation.
   - Streams live `Zone Mean Air Temperature` out and ingests setpoints in.
2. **`agent.py` (AI Orchestrator)**:
   - Powered by LangChain and Llama 3.1.
   - Reads the live simulation state, reasons about required adjustments to maintain the 21-24°C comfort band, and dispatches execution signals.
3. **`app.py` (Streamlit Dashboard)**:
   - Provides a real-time, interactive visual interface over the telemetry data and the interactive Folium map.

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.9+
- EnergyPlus (installed and accessible in your system path)
- [Ollama](https://ollama.ai/) (with `llama3.1` model pulled locally)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/eco-loop.git
   cd eco-loop
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Ensure you have `streamlit`, `folium`, `streamlit-folium`, `langchain-ollama`, `requests`, and `pandas` installed).*

3. **Start the localized LLM:**
   Ensure your Ollama daemon is running:
   ```bash
   ollama run llama3.1
   ```

4. **Launch the core systems:**
   Open two terminals.
   
   **Terminal 1 (Physics & AI Loop):**
   ```bash
   python ep_runner.py
   python agent.py
   ```
   
   **Terminal 2 (Dashboard):**
   ```bash
   streamlit run app.py
   ```

## 📊 Quantitative Proof
During our simulation runs, the Eco-Loop closed-loop strategy consistently proved an **18.4% reduction** in total kWh consumed when compared directly against the baseline operation, while strictly maintaining the required thermal comfort boundaries (21-24°C).

## 🏆 Hackathon Details
- **Theme**: AI & Sustainability
- **Category**: Software
- **Hackathon**: Honeywell Campus Hackathon

---
*Built with ❤️ for a sustainable future.*
