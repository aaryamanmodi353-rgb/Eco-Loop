import subprocess
import os

def run_baseline():
    ep_path = os.path.join("EnergyPlus", "EnergyPlus-23.2.0-7636e6b3e9-Windows-x86_64", "energyplus.exe")
    idf_file = "baseline.idf"
    epw_file = "weather.epw"
    
    print(f"Running baseline simulation with {idf_file} and {epw_file}...")
    
    # Run the EnergyPlus simulation
    result = subprocess.run([
        ep_path, 
        "--weather", epw_file,
        "--output-directory", "baseline_results",
        idf_file
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Baseline simulation completed successfully!")
        print("Results are stored in the 'baseline_results' directory.")
    else:
        print("Error running simulation. Return code:", result.returncode)
        print("--- STDOUT ---")
        print(result.stdout)
        print("--- STDERR ---")
        print(result.stderr)

if __name__ == "__main__":
    run_baseline()
