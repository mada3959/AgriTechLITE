from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import pickle
import numpy as np
from flask import jsonify

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agritechlite!'
socketio = SocketIO(app, cors_allowed_origins="*")

model = pickle.load(open(r'C:\Users\ACER\Documents\Arduino\AgriTechLITE\models\RandomForest.pkl', 'rb'))

class_names = [
    'rice', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas',
    'mothbeans', 'mungbean', 'blackgram', 'lentil', 'pomegranate',
    'banana', 'mango', 'grapes', 'watermelon', 'muskmelon', 'apple',
    'orange', 'papaya', 'coconut', 'cotton', 'jute', 'coffee'
]

sensor_data = {
    "cahaya": 0,
    "suhu": 0,
    "kelembapan_udara": 0,
    "hujan": 0,
    "kelembapan_tanah": 0,
    "hujanV": 0,
    "humtanah": 0
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

@app.route('/ML', methods=['POST'])
def predict():
    try:
        features = [
            round(sensor_data['suhu'], 1),
            round(sensor_data['kelembapan_udara'], 1),
            round(sensor_data['hujanV'], 1),
            round(sensor_data['humtanah'], 1)
        ]
        input_array = np.array([features])
        prediction = model.predict(input_array)
        predicted_class = class_names[int(prediction[0])]

        return jsonify({'class': predicted_class})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

if __name__ == '__main__':
   socketio.run(app, host="0.0.0.0", port=5000, debug=True)