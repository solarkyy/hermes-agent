import os
import subprocess
import logging

logger = logging.getLogger(__name__)

def _on_session_start(**kwargs):
    # Locate the omni-seat script
    omnios_dir = os.path.expanduser("~/Desktop/omnios")
    script = os.path.join(omnios_dir, "scripts", "omni-seat.sh")
    
    if not os.path.exists(script):
        logger.warning(f"omni-seat script not found at {script}")
        return

    try:
        # Get environment exports from omni-seat env
        out = subprocess.check_output([script, "env"], text=True)
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("export "):
                # Parse e.g., export OMNIOS_ROOT='/home/kyle/Desktop/omnios'
                key_val = line[7:].split("=", 1)
                if len(key_val) == 2:
                    k = key_val[0].strip()
                    v = key_val[1].strip("'\"")
                    if k == "PATH":
                        # Be careful not to wipe out the current PATH, though omni-seat
                        # normally prepends to it securely. We'll set it as provided.
                        os.environ["PATH"] = v
                    else:
                        os.environ[k] = v
        
        # Print status to user terminal for organism awareness
        print("\n\033[38;5;39m[OMNI-SEAT]\033[0m \033[3mBooting organism context...\033[0m")
        subprocess.run([script, "status"], check=False)
        
    except Exception as e:
        logger.error(f"omni-seat boot failed: {e}")

def register(ctx):
    """Register the omni-seat plugin with Hermes."""
    ctx.register_hook("on_session_start", _on_session_start)
