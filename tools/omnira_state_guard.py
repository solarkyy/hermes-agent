import json

def state_guarded(tool_name):
    def decorator(func):
        def wrapper(args, **kw):
            # 1. Parse arguments from the tool
            is_state_probe = args.get("is_state_probe", False)
            justification = args.get("justification_receipt", "")
            
            # 2. Check the command for obvious read-only probes
            # If it's explicitly marked as a probe, or has a justification, we let it pass.
            if is_state_probe:
                # Let it run, it's just looking.
                return func(args, **kw)
            
            if justification and len(justification.strip()) > 5:
                # The agent provided a state receipt justifying this action.
                return func(args, **kw)
                
            # 3. No justification, not a probe. Is it a modifying command?
            # We'll use a simple heuristic for terminal. File operations are inherently modifying unless it's read.
            if tool_name == "terminal":
                cmd = args.get("command", "").strip()
                read_only_prefixes = ["ls ", "cat ", "grep ", "find ", "ps ", "ss ", "ping ", "git status", "git log", "echo ", "tail ", "head ", "whoami", "pwd", "systemctl status"]
                if any(cmd.startswith(prefix) for prefix in read_only_prefixes):
                    # It's a read-only terminal probe, let it pass even without the flag
                    return func(args, **kw)
            
            # 4. Membrane Violation
            return json.dumps({
                "error": "OMNIRA MEMBRANE VIOLATION: ACTION BLOCKED",
                "reason": f"You attempted to execute a potentially modifying {tool_name} command based on a [CLAIM], but provided no [STATE] justification receipt.",
                "remediation": "You must execute a read-only `is_state_probe=true` command first to verify the claim. Then run this command again, including the probe's output in the `justification_receipt` argument."
            })
        return wrapper
    return decorator
