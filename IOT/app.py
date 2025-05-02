from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import pickle
import numpy as np
import csv
import os
from models import db, Plant  # models.py berisi definisi class Plant & db = SQLAlchemy()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'agritechlite!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)

model = pickle.load(open('models/RandomForest.pkl', 'rb'))

label_mapping = {
    'rice': 'Padi', 'maize': 'Jagung', 'chickpea': 'Kacang Arab',
    'kidneybeans': 'Kacang Merah', 'pigeonpeas': 'Kacang Gude', 'mothbeans': 'Kacang Moth',
    'mungbean': 'Kacang Hijau', 'blackgram': 'Kacang Hitam', 'lentil': 'Kacang Lentil',
    'pomegranate': 'Delima', 'banana': 'Pisang', 'mango': 'Mangga', 'grapes': 'Anggur',
    'watermelon': 'Semangka', 'muskmelon': 'Melon', 'apple': 'Apel', 'orange': 'Jeruk',
    'papaya': 'Pepaya', 'coconut': 'Kelapa', 'cotton': 'Kapas', 'jute': 'Goni', 'coffee': 'Kopi'
}

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

def create_tables_and_load_data():
    db.create_all()
    if not Plant.query.first():
        with open('plants-information.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                plant = Plant(
                    name=row['name'],
                    image_url=row['image_url'],
                    overview=row['overview'],
                    tools=row['tools_materials'],
                    harvest=row['harvest_method'],
                    maintenance=row['care_tips'],
                    illness=row['sickness_solution'],
                    small_land_tips=row['limited_land_tip'],
                    harvest_day=row['harvest_day']
                )
                db.session.add(plant)
            db.session.commit()

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
        data = request.get_json()
        print("Data yang diterima untuk prediksi:", data)
        features = [
            round(data.get('suhu', 0), 1),
            round(data.get('kelembapan_udara', 0), 1),
            round(data.get('hujanV', 0), 1),
            round(data.get('humtanah', 0), 1)
        ]
        input_array = np.array([features])
        prediction = model.predict(input_array)
        raw_label = prediction[0].lower()
        mapped_name = label_mapping.get(raw_label)

        if not mapped_name:
            return jsonify({'class': raw_label, 'error': 'Tanaman tidak ditemukan dalam mapping'}), 404

        matched_plant = Plant.query.filter(Plant.name.ilike(mapped_name)).first()
        if matched_plant:
            return jsonify({
                'class': matched_plant.name,
                'image_url': matched_plant.image_url,
                'overview': matched_plant.overview,
                'tools': matched_plant.tools,
                'harvest': matched_plant.harvest,
                'maintenance': matched_plant.maintenance,
                'illness': matched_plant.illness,
                'small_land_tips': matched_plant.small_land_tips,
                'harvest_day': matched_plant.harvest_day
            })
        else:
            return jsonify({'class': mapped_name, 'error': 'Tanaman tidak ditemukan di database'}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR DI /ML:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        create_tables_and_load_data()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)