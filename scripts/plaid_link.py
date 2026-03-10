"""
One-time Plaid account linking for Capital One Spark.

Run this ONCE to connect your Capital One account to Plaid.
It will open a browser window — log into Capital One when prompted.
After linking, it prints your access token — paste it into backend/.env

Usage:
    cd Transaction_Tracker
    pip install -r backend/requirements.txt
    python scripts/plaid_link.py
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "backend" / ".env")

import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from flask import Flask, request, jsonify, redirect
import webbrowser
import threading
import time

PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.environ.get("PLAID_SECRET", "")
PLAID_ENV = os.environ.get("PLAID_ENV", "production")

env_map = {
    "sandbox": plaid.Environment.Sandbox,
    "development": plaid.Environment.Development,
    "production": plaid.Environment.Production,
}

config = plaid.Configuration(
    host=env_map.get(PLAID_ENV, plaid.Environment.Production),
    api_key={"clientId": PLAID_CLIENT_ID, "secret": PLAID_SECRET}
)
plaid_client = plaid_api.PlaidApi(plaid.ApiClient(config))

app = Flask(__name__)
_access_token = None


@app.route("/")
def index():
    # Create a link token
    req = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Masterson Transaction Tracker",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id="masterson-admin"),
        webhook="https://your-railway-app.up.railway.app/webhook/plaid"  # update after deploy
    )
    resp = plaid_client.link_token_create(req)
    link_token = resp["link_token"]

    # Simple HTML page that opens Plaid Link
    return f"""
    <html><head><title>Plaid Link</title></head>
    <body style="font-family:Arial;padding:40px;background:#111;color:white;">
    <h2>Masterson — Link Capital One Account</h2>
    <p>Click below and log into your Capital One Spark account.</p>
    <button id="linkBtn" style="padding:15px 30px;font-size:18px;cursor:pointer;">
      🔗 Connect Capital One
    </button>
    <div id="status" style="margin-top:20px;color:#0f0;"></div>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <script>
      var handler = Plaid.create({{
        token: '{link_token}',
        onSuccess: function(public_token, metadata) {{
          document.getElementById('status').innerText = 'Exchanging token...';
          fetch('/exchange', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{public_token: public_token}})
          }}).then(r => r.json()).then(d => {{
            document.getElementById('status').innerHTML =
              '<b>✅ Linked!</b><br>Copy this into your backend/.env as PLAID_ACCESS_TOKEN:<br><br><code style="background:#222;padding:10px;display:block;">' + d.access_token + '</code>';
          }});
        }},
        onExit: function(err) {{
          if (err) document.getElementById('status').innerText = 'Error: ' + JSON.stringify(err);
        }}
      }});
      document.getElementById('linkBtn').onclick = function() {{ handler.open(); }};
    </script>
    </body></html>
    """


@app.route("/exchange", methods=["POST"])
def exchange():
    global _access_token
    public_token = request.json["public_token"]
    req = ItemPublicTokenExchangeRequest(public_token=public_token)
    resp = plaid_client.item_public_token_exchange(req)
    _access_token = resp["access_token"]
    print(f"\n{'='*60}")
    print("SUCCESS! Add this to backend/.env:")
    print(f"PLAID_ACCESS_TOKEN={_access_token}")
    print('='*60)
    return jsonify({"access_token": _access_token})


def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5555")


if __name__ == "__main__":
    if not PLAID_CLIENT_ID or not PLAID_SECRET:
        print("[error] PLAID_CLIENT_ID and PLAID_SECRET must be set in backend/.env")
        sys.exit(1)
    print("Opening browser for Plaid Link...")
    print("Log into Capital One when prompted.")
    print("After linking, copy the access token into backend/.env\n")
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(port=5555, debug=False)
