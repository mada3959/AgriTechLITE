from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agritechlite!'
socketio = SocketIO(app, cors_allowed_origins="*")

sensor_data = {
    "cahaya": 0,
    "suhu": 0,
    "kelembapan": 0,
    "hujan": 0
}
pompa_status = "OFF"

@app.route('/')
def index():
    return render_template('index.html', pompa_status=pompa_status)

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_data
    sensor_data = request.get_json()
    socketio.emit('update_sensor', sensor_data)  # Kirim update ke semua client
    return "OK", 200

@app.route('/control', methods=['POST'])
def control():
    global pompa_status
    action = request.form['action']
    if action == "ON":
        pompa_status = "ON"
    elif action == "OFF":
        pompa_status = "OFF"
    socketio.emit('update_pompa', {"pompa_status": pompa_status})
    return render_template('index.html', pompa_status=pompa_status)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)