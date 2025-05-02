from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pickle
import numpy as np
import csv
import os
from models import db, Plant

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

model = pickle.load(open('models/RandomForest.pkl', 'rb'))

label_mapping = {
    'rice': 'Padi',
    'maize': 'Jagung',
    'chickpea': 'Kacang Arab',
    'kidneybeans': 'Kacang Merah',
    'pigeonpeas': 'Kacang Gude',
    'mothbeans': 'Kacang Moth',
    'mungbean': 'Kacang Hijau',
    'blackgram': 'Kacang Hitam',
    'lentil': 'Kacang Lentil',
    'pomegranate': 'Delima',
    'banana': 'Pisang',
    'mango': 'Mangga',
    'grapes': 'Anggur',
    'watermelon': 'Semangka',
    'muskmelon': 'Melon',
    'apple': 'Apel',
    'orange': 'Jeruk',
    'papaya': 'Pepaya',
    'coconut': 'Kelapa',
    'cotton': 'Kapas',
    'jute': 'Goni',
    'coffee': 'Kopi'
}

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
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        features = [
            round(float(data['suhu']), 1),
            round(float(data['kelembapan_udara']), 1),
            round(float(data['hujan']), 1),
            round(float(data['kelembapan_tanah']), 1)
        ]
        input_array = np.array([features])
        prediction = model.predict(input_array)
        raw_label = prediction[0].lower()

        print(f"🎯 Hasil prediksi mentah: {raw_label}")
        mapped_name = label_mapping.get(raw_label)
        print(f"✅ Label prediksi setelah mapping: {mapped_name}")

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
            print("⚠️ Tanaman tidak ditemukan di database.")
            return jsonify({'class': mapped_name, 'error': 'Tanaman tidak ditemukan di database'}), 404

    except Exception as e:
        print("🔥 Error:", e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        create_tables_and_load_data()
    app.run(debug=True)
