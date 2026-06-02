import os
import sys
import json
import base64
import hashlib
import time
import uuid
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

def get_auth_dir():
    d = Path.home() / ".hermes" / "auth"
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d

def get_oauth_dir():
    d = get_auth_dir() / "oauth"
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d

def get_receipts_dir():
    d = get_auth_dir() / "receipts"
    d.mkdir(parents=True, exist_ok=True)
    d.chmod(0o700)
    return d

def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
    return verifier, challenge

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.server.oauth_code = qs.get("code", [None])[0]
        self.server.oauth_state = qs.get("state", [None])[0]
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><h1>OAuth Authentication Complete</h1><p>You can close this window.</p></body></html>")

    def log_message(self, format, *args):
        pass

def do_login(provider, client_id, auth_url, token_url, scopes):
    state = str(uuid.uuid4())
    verifier, challenge = generate_pkce_pair()
    
    server = HTTPServer(('127.0.0.1', 0), CallbackHandler)
    port = server.server_port
    redirect_uri = f"http://127.0.0.1:{port}"
    
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "scope": " ".join(scopes)
    }
    
    auth_req_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    print(f"Opening browser for {provider} login...")
    webbrowser.open(auth_req_url)
    
    server.handle_request()
    
    if server.oauth_state != state:
        print("Error: State mismatch! Potential CSRF attack.")
        return 1
        
    if not server.oauth_code:
        print("Error: No code received.")
        return 1
        
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "client_id": client_id,
        "code": server.oauth_code,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier
    }).encode("utf-8")
    
    req = urllib.request.Request(token_url, data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"Token exchange failed: {e}")
        return 1
        
    token_file = get_oauth_dir() / f"{provider}.json"
    with open(token_file, "w") as f:
        json.dump(token_data, f, indent=2)
    token_file.chmod(0o600)
    
    receipt = {
        "action": "oauth_login",
        "provider": provider,
        "status": "success",
        "ts": time.time(),
        "training_eligible": False,
        "promotion_eligible": False
    }
    receipt_file = get_receipts_dir() / f"rcpt-{int(time.time())}-oauth-{provider}.json"
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)
    receipt_file.chmod(0o600)
    
    print(f"Successfully logged into {provider}")
    return 0

def do_status(provider):
    token_file = get_oauth_dir() / f"{provider}.json"
    if token_file.exists():
        print(f"{provider}: Authenticated")
    else:
        print(f"{provider}: Not authenticated")
    return 0

def do_logout(provider):
    token_file = get_oauth_dir() / f"{provider}.json"
    if token_file.exists():
        token_file.unlink()
        print(f"Logged out of {provider}")
    else:
        print(f"Not logged into {provider}")
    return 0

def main(argv):
    if len(argv) < 1:
        print("Usage: [login|refresh|status|logout] [provider config json]")
        return 1
        
    cmd = argv[0]
    provider_config_json = argv[1] if len(argv) > 1 else "{}"
    
    try:
        config = json.loads(provider_config_json)
    except json.JSONDecodeError:
        config = {"provider": provider_config_json}
        
    provider = config.get("provider", "example-provider")
    client_id = config.get("client_id", "example-client")
    auth_url = config.get("auth_url", "https://example.com/auth")
    token_url = config.get("token_url", "https://example.com/token")
    scopes = config.get("scopes", ["profile"])
    
    if cmd == "login":
        return do_login(provider, client_id, auth_url, token_url, scopes)
    elif cmd == "status":
        return do_status(provider)
    elif cmd == "logout":
        return do_logout(provider)
    elif cmd == "refresh":
        # Placeholder for refresh logic
        print(f"Refreshed {provider}")
        return 0
    else:
        print(f"Unknown command {cmd}")
        return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
