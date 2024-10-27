import subprocess
import time

import psutil  


def run_with_timeout(command, timeout):
    start_time = time.time()
    process = subprocess.Popen(command, shell=True)
    while process.poll() is None:
        time.sleep(1)
        if time.time() - start_time > timeout:
            process.terminate()  
            process.wait()
            return None
    return process.returncode



command = "python visualization.py"
timeout_seconds = 50
return_code = run_with_timeout(command, timeout_seconds)
if return_code is None:
    print("Process terminated due to timeout.")
else:
    print(f"Process exited with return code {return_code}.")
