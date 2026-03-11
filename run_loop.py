import subprocess
import time
import re
import os
from datetime import datetime

RESULTS_FILE = "results.tsv"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run_training_loop():
    # Initialize results file
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "w") as f:
            f.write("Timestamp\tRun_ID\tVal_BPB\tMin_Val_BPB\n")
            
    # Read existing minimum if file exists and has data
    min_val_bpb = float('inf')
    run_id = 1
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r") as f:
            lines = f.readlines()
            if len(lines) > 1:
                # Get max Run_ID
                last_line = lines[-1].strip().split("\t")
                if len(last_line) >= 4:
                    run_id = int(last_line[1]) + 1
                
                # Find current min
                for line in lines[1:]:
                    parts = line.strip().split("\t")
                    if len(parts) >= 3:
                        try:
                            val = float(parts[2])
                            if val < min_val_bpb:
                                min_val_bpb = val
                        except ValueError:
                            pass

    print(f"Starting automated training loop. Current Min BPB: {min_val_bpb if min_val_bpb != float('inf') else 'None'}")
    
    while True:
        print(f"\n[{get_timestamp()}] Staring Run #{run_id}...")
        
        # Run the training script
        # Using subprocess.Popen to stream output to console while capturing it
        process = subprocess.Popen(
            ["uv", "run", "train.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        output_lines = []
        for line in process.stdout:
            print(line, end="") # Stream to console
            output_lines.append(line)
            
        process.wait()
        
        if process.returncode != 0:
            print(f"\n[{get_timestamp()}] Run #{run_id} failed with exit code {process.returncode}. Retrying in 10s...")
            time.sleep(10)
            continue
            
        # Parse output for val_bpb
        output_text = "".join(output_lines)
        match = re.search(r"val_bpb:\s+([0-9.]+)", output_text)
        
        if match:
            current_bpb = float(match.group(1))
            if current_bpb < min_val_bpb:
                print(f"*** NEW MINIMUM BPB: {current_bpb} (was {min_val_bpb}) ***")
                min_val_bpb = current_bpb
                
            # Log results
            with open(RESULTS_FILE, "a") as f:
                f.write(f"{get_timestamp()}\t{run_id}\t{current_bpb:.6f}\t{min_val_bpb:.6f}\n")
                
            print(f"[{get_timestamp()}] Run #{run_id} completed. Val BPB: {current_bpb:.6f} | Min BPB: {min_val_bpb:.6f}")
        else:
            print(f"[{get_timestamp()}] Warning: Could not find val_bpb in output for Run #{run_id}")
            
        run_id += 1

if __name__ == "__main__":
    try:
        run_training_loop()
    except KeyboardInterrupt:
        print("\nAutomated training loop stopped by user.")
