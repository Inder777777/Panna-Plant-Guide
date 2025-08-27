# File: server.py

# Crucial: Monkey patch the standard library for eventlet.
# This MUST be the first thing that happens.
import eventlet
eventlet.monkey_patch()

# Now, import all other modules
import asyncio
from flask import Flask, request
from flask_socketio import SocketIO, emit
import random

# --- Configuration ---
OPC_UA_SERVER_URL = "opc.tcp://your_opc_ua_server_ip:4840/freeopcua/server/"
NODES_TO_MONITOR = {
    "PREHEATER_EXIT_TEMP": "ns=2;i=20",
    "KILN_FEED_END_TEMP": "ns=2;i=21",
    "COOLER_EXIT_TEMP": "ns=2;i=22",
    "CLINKER_TONS_PER_HOUR": "ns=2;i=23",
}

# --- Mock User Database for Authentication ---
VALID_CREDENTIALS = {
    "user": "password123"
}

# --- Flask App and SocketIO Initialization ---
app = Flask(__name__)
# The secret key is good practice for production
app.config['SECRET_KEY'] = 'a_very_secret_key!'

# --- MODIFIED LINE: Explicitly set async_mode to 'eventlet' ---
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')


# --- OPC UA CLIENT SIMULATOR (using socketio.sleep for compatibility) ---
class OpcuaClientSimulator:
    def __init__(self, nodes):
        self.node_names = list(nodes.keys())
        self.is_monitoring = True

    def monitor_nodes(self):
        """Continuously generates and sends random data updates."""
        print("--- RUNNING IN SIMULATION MODE with eventlet ---")
        
        while self.is_monitoring:
            for name in self.node_names:
                value = 0.0
                if name == "PREHEATER_EXIT_TEMP":
                    value = random.uniform(1440.0, 1465.0)
                elif name == "KILN_FEED_END_TEMP":
                    value = random.uniform(98.0, 103.5)
                elif name == "COOLER_EXIT_TEMP":
                    value = random.uniform(99.0, 105.0)
                elif name == "CLINKER_TONS_PER_HOUR":
                    value = random.uniform(198.0, 203.0)
                else:
                    value = random.uniform(0.0, 100.0)
                
                print(f"Simulated {name}: {round(value, 2)}")
                socketio.emit('plant_data_update', {'name': name, 'value': round(value, 2)})

            # Use socketio.sleep, which is compatible with eventlet
            socketio.sleep(2) 
            
        print("Simulation stopped.")

# --- Instantiate the client ---
opcua_client = OpcuaClientSimulator(NODES_TO_MONITOR)

# --- Start the simulator as a background task ---
# We need to run this within the app context for it to work correctly with socketio
def start_simulator():
    opcua_client.monitor_nodes()

socketio.start_background_task(target=start_simulator)


# --- Flask Routes and SocketIO Events ---
@app.route('/login', methods=['POST'])
def login():
    """Handles user authentication."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in VALID_CREDENTIALS and VALID_CREDENTIALS[username] == password:
        return {'status': 'success', 'message': 'Login successful'}
    else:
        return {'status': 'error', 'message': 'Invalid credentials'}, 401

@socketio.on('connect')
def handle_connect():
    """A new client has connected."""
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    """A client has disconnected."""
    print('Client disconnected')

# --- NEW `if __name__ == '__main__':` block for eventlet ---
if __name__ == '__main__':
    # socketio.run() will use the eventlet server because of the async_mode setting
    socketio.run(app, host='0.0.0.0', port=5000)