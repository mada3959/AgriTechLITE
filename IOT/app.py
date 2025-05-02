from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agritechlite!'
socketio = SocketIO(app, cors_allowed_origins="*")

sensor_data = {
    "cahaya": 0,
    "suhu": 0,
    "kelembapan_udara": 0,
    "hujan": 0,
    "kelembapan_tanah": 0
}
pompa_status = "OFF"

@app.route('/')
def index():
    return render_template('index.html', pompa_status=pompa_status)

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_data
    try:
        sensor_data = request.get_json()
        socketio.emit('update_sensor', sensor_data)
        return "OK", 200
    except Exception as e:
        return f"Error: {str(e)}", 400

@app.route('/pompa', methods=['POST'])
def control_pompa():
    global pompa_status
    action = request.form.get('action', '')
    if action in ["ON", "OFF"]:
        pompa_status = action
        socketio.emit('update_pompa', {"pompa_status": pompa_status})
        return '', 204
    return 'Invalid Action', 400

@app.route('/pompa/status', methods=['GET'])
def get_pompa_status():
    return pompa_status, 200

if __name__ == '__main__':
   socketio.run(app, host="0.0.0.0", port=5000, debug=True)
