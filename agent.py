import json
import os
import time
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


@tool
def get_building_state() -> str:
    """Reads the current state of the building simulation including zone temperatures and time."""
    try:
        with open("state.json", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "Simulation state not available yet."

@tool
def set_hvac_setpoints(heating_setpoint: float, cooling_setpoint: float) -> str:
    """
    Sets the HVAC thermostats for the building.
    Args:
        heating_setpoint: The heating setpoint in Celsius (e.g. 21.0). Must be strictly lower than cooling.
        cooling_setpoint: The cooling setpoint in Celsius (e.g. 24.0). Must be strictly higher than heating.
    """
    if heating_setpoint >= cooling_setpoint:
        return "Error: Heating setpoint must be lower than cooling setpoint to prevent deadband fighting."
        
    action = {
        "heating_setpoint": heating_setpoint,
        "cooling_setpoint": cooling_setpoint
    }
    with open("action.json", "w") as f:
        json.dump(action, f)
        
    return f"Successfully sent command to update setpoints to Heating: {heating_setpoint}C, Cooling: {cooling_setpoint}C"

tools = [get_building_state, set_hvac_setpoints]

# Initialize LLM
llm = ChatOllama(model="llama3.1", temperature=0.1)
llm_with_tools = llm.bind_tools(tools)

system_prompt = """You are an autonomous Eco-Loop Building Agent. Your goal is to manage the HVAC system of a 5-zone building to minimize energy consumption while maintaining thermal comfort (Zone temperatures between 21.0C and 24.0C).

You run in a continuous closed-loop:
1. Read the building state (including Zone Temperatures and Outdoor Temperature).
2. Analyze the temperatures. If they are drifting out of the comfort zone, adjust the setpoints.
3. PREDICTIVE CONTROL: Look at the Outdoor_Temp_C. If it's cold outside, use a lower heating setpoint. If it's hot outside, use a higher cooling setpoint to save energy!
4. If the building is already comfortable, try to relax the setpoints to save energy.

CRITICAL RULES:
- Never let heating setpoint >= cooling setpoint.
- Only call the tools, do not output raw text."""

def run_agent_loop():
    print("Starting Eco-Loop Cognitive Engine...")
    
    while True:
        if not os.path.exists("state.json"):
            print("Waiting for EnergyPlus simulation to start...")
            time.sleep(2)
            continue
            
        print("\n--- Invoking Agent ---")
        try:
            messages = [
                ("system", system_prompt),
                ("human", "Check the current building state and adjust setpoints if necessary.")
            ]
            
            # 1. Invoke the LLM to get tool calls
            ai_msg = llm_with_tools.invoke(messages)
            
            # Log the thought stream
            thought_text = ai_msg.content if ai_msg.content else "No explicit reasoning provided."
            with open("thoughts.txt", "w") as f:
                f.write(thought_text)
            
            # 2. Execute any tools it requested
            if ai_msg.tool_calls:
                for tool_call in ai_msg.tool_calls:
                    print(f"Agent Action -> {tool_call['name']}: {tool_call['args']}")
                    
                    # Log action to thoughts
                    with open("thoughts.txt", "a") as f:
                        f.write(f"\n\n**Action:** Called `{tool_call['name']}` with {tool_call['args']}")
                        
                    if tool_call["name"] == "get_building_state":
                        result = get_building_state.invoke(tool_call["args"])
                        print(f"State: {result}")
                    elif tool_call["name"] == "set_hvac_setpoints":
                        result = set_hvac_setpoints.invoke(tool_call["args"])
                        
                        # Increment invocation counter for dashboard
                        invocations = 0
                        if os.path.exists("invocations.txt"):
                            with open("invocations.txt", "r") as f:
                                invocations = int(f.read().strip())
                        with open("invocations.txt", "w") as f:
                            f.write(str(invocations + 1))
                            
                        print(f"Command Result: {result}")
            else:
                print("Agent chose to do nothing.")
                
        except Exception as e:
            error_msg = f"Agent encountered a critical error:\n{e}"
            print(error_msg)
            with open("thoughts.txt", "w") as f:
                f.write(error_msg)
        print("Sleeping for supervisory control period...")
        time.sleep(5)

if __name__ == "__main__":
    run_agent_loop()
