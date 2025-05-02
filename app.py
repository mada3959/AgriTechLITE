from flask import Flask, render_template, Response, request, jsonify, request
import pickle
import numpy as np

app = Flask(__name__)

sensor_data = {
    "cahaya": 0,
    "suhu": 0,
    "kelembapan_udara": 0,
    "hujan": 0,
    "kelembapan_tanah": 0
}

model = pickle.load(open('models/RandomForest.pkl', 'rb'))

@app.route('/')
def index():
    return render_template('index.html')

class_names = [
    'rice', 'maize', 'chickpea', 'kidneybeans', 'pigeonpeas',
    'mothbeans', 'mungbean', 'blackgram', 'lentil', 'pomegranate',
    'banana', 'mango', 'grapes', 'watermelon', 'muskmelon', 'apple',
    'orange', 'papaya', 'coconut', 'cotton', 'jute', 'coffee'
]

@app.route('/predict', methods=['GET'])
def predict():
    try:
        features = [
            round(sensor_data['suhu'], 1),
            round(sensor_data['kelembapan_udara'], 1),
            round(sensor_data['hujan'], 1),
            round(sensor_data['kelembapan_tanah'], 1)
        ]
        input_array = np.array([features])
        prediction = model.predict(input_array)
        predicted_class = class_names[np.argmax(prediction)]

        return jsonify({'class': predicted_class})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
