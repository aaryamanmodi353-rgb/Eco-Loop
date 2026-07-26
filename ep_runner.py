import sys
import os
import json
import time

# Add EnergyPlus Python API to path
ep_install_path = os.path.abspath(os.path.join("EnergyPlus", "EnergyPlus-23.2.0-7636e6b3e9-Windows-x86_64"))
sys.path.insert(0, ep_install_path)

from pyenergyplus.api import EnergyPlusAPI

api = EnergyPlusAPI()
state = api.state_manager.new_state()

zones = ["SPACE1-1", "SPACE2-1", "SPACE3-1", "SPACE4-1", "SPACE5-1"]
var_handles = {}
act_handles = {}
initialized = False

# Request variables before simulation starts
for z in zones:
    api.exchange.request_variable(state, "Zone Mean Air Temperature", z)
api.exchange.request_variable(state, "Site Outdoor Air Drybulb Temperature", "Environment")

def callback(state):
    global initialized, var_handles, act_handles
    
    # Wait until the API is fully ready
    if not api.exchange.api_data_fully_ready(state):
        return
        
    if not initialized:
        # Get handles for sensors
        for z in zones:
            var_handles[z] = api.exchange.get_variable_handle(state, "Zone Mean Air Temperature", z)
            
        # Get handles for actuators (Thermostat Setpoint Schedules)
        act_handles["heating"] = api.exchange.get_actuator_handle(state, "Schedule:Compact", "Schedule Value", "HTG-SETP-SCH")
        act_handles["cooling"] = api.exchange.get_actuator_handle(state, "Schedule:Compact", "Schedule Value", "CLG-SETP-SCH")
        initialized = True

    # 1. EXTRACT STATE (Feedback)
    outdoor_handle = api.exchange.get_variable_handle(state, "Site Outdoor Air Drybulb Temperature", "Environment")
    current_state = {
        "time": api.exchange.current_sim_time(state),
        "day_of_week": api.exchange.day_of_week(state),
        "hour": api.exchange.hour(state),
        "Outdoor_Temp_C": round(api.exchange.get_variable_value(state, outdoor_handle), 2) if outdoor_handle > 0 else 20.0
    }
    for z in zones:
        val = api.exchange.get_variable_value(state, var_handles[z])
        current_state[f"{z}_Temp_C"] = round(val, 2)
        
    # Write the latest state to disk for the MCP Server to read
    with open("state.json", "w") as f:
        json.dump(current_state, f)
        
    # Append to history for the dashboard
    csv_header = "time,day_of_week,hour,Outdoor_Temp_C,SPACE1-1_Temp_C,SPACE2-1_Temp_C,SPACE3-1_Temp_C,SPACE4-1_Temp_C,SPACE5-1_Temp_C\n"
    if not os.path.exists("ai_history.csv"):
        with open("ai_history.csv", "w") as f:
            f.write(csv_header)
    with open("ai_history.csv", "a") as f:
        f.write(f"{current_state['time']},{current_state['day_of_week']},{current_state['hour']},{current_state['Outdoor_Temp_C']},{current_state['SPACE1-1_Temp_C']},{current_state['SPACE2-1_Temp_C']},{current_state['SPACE3-1_Temp_C']},{current_state['SPACE4-1_Temp_C']},{current_state['SPACE5-1_Temp_C']}\n")
        
    # 2. INJECT ACTIONS (Forward Injection)
    # Check if the AI has provided a new action
    if os.path.exists("action.json"):
        try:
            with open("action.json", "r") as f:
                action = json.load(f)
            
            # Apply setpoints if they exist in the action payload
            if "heating_setpoint" in action:
                api.exchange.set_actuator_value(state, act_handles["heating"], action["heating_setpoint"])
                print(f"[{current_state['hour']}:00] AI updated Heating Setpoint to {action['heating_setpoint']} C")
                
            if "cooling_setpoint" in action:
                api.exchange.set_actuator_value(state, act_handles["cooling"], action["cooling_setpoint"])
                print(f"[{current_state['hour']}:00] AI updated Cooling Setpoint to {action['cooling_setpoint']} C")
                
            # Consume the action file so we don't apply it twice
            os.remove("action.json")
        except Exception as e:
            # File might be locked during writing by MCP, just skip this timestep
            pass
            
    # Add a tiny sleep so the simulation doesn't run so fast the AI can't keep up in our PoC
    time.sleep(0.01)

# Register the callback hook
api.runtime.callback_begin_zone_timestep_after_init_heat_balance(state, callback)

print("Starting AI-Ready EnergyPlus Simulation Loop...")
# Run the simulation, outputting to a new 'ai_results' folder
api.runtime.run_energyplus(state, ["-w", "weather.epw", "-d", "ai_results", "baseline.idf"])
print("Simulation Complete!")
