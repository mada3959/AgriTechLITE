from flask import Flask, render_template, request, jsonify          # Import modul Flask untuk web server dan handling request
from flask_socketio import SocketIO, emit                           # Import untuk komunikasi real-time via WebSocket
from flask_sqlalchemy import SQLAlchemy                             # Import untuk ORM dan manajemen database
import pickle                                                       # Untuk load model machine learning yang sudah disimpan
import numpy as np                                                  # Untuk manipulasi array numerik
import csv                                                          # Untuk membaca file CSV
import os                                                           # Untuk operasi file system
from models import db, Plant                                        # Import definisi database dan tabel Plant dari models.py

app = Flask(__name__)                                               # Inisialisasi aplikasi Flask
app.config['SECRET_KEY'] = 'agritechlite!'                          # Kunci rahasia Flask
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///plants.db'      # Lokasi file database SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False               # Nonaktifkan notifikasi tracking perubahan (menghemat resource)

socketio = SocketIO(app, cors_allowed_origins="*")                 # Inisialisasi SocketIO untuk komunikasi real-time
db.init_app(app)                                                    # Hubungkan objek database dengan aplikasi Flask

model = pickle.load(open('models/RandomForest.pkl', 'rb'))         # Load model machine learning yang sudah dipickle

# Mapping label hasil prediksi ke nama tanaman dalam Bahasa Indonesia
label_mapping = {
    'rice': 'Padi', 'maize': 'Jagung', 'chickpea': 'Kacang Arab',
    'kidneybeans': 'Kacang Merah', 'pigeonpeas': 'Kacang Gude', 'mothbeans': 'Kacang Moth',
    'mungbean': 'Kacang Hijau', 'blackgram': 'Kacang Hitam', 'lentil': 'Kacang Lentil',
    'pomegranate': 'Delima', 'banana': 'Pisang', 'mango': 'Mangga', 'grapes': 'Anggur',
    'watermelon': 'Semangka', 'muskmelon': 'Melon', 'apple': 'Apel', 'orange': 'Jeruk',
    'papaya': 'Pepaya', 'coconut': 'Kelapa', 'cotton': 'Kapas', 'jute': 'Goni', 'coffee': 'Kopi'
}

# Variabel global untuk menyimpan data sensor terkini
sensor_data = {
    "cahaya": 0,
    "suhu": 0,
    "kelembapan_udara": 0,
    "hujan": 0,
    "kelembapan_tanah": 0,
    "hujanV": 0,
    "humtanah": 0
}
pompa_status = "OFF"  # Status default pompa saat server baru berjalan

# Fungsi untuk membuat tabel database dan load data tanaman dari file CSV
def create_tables_and_load_data():
    db.create_all()  # Buat semua tabel berdasarkan model
    if not Plant.query.first():  # Cek jika data tanaman belum ada di database
        with open('plants-information.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                plant = Plant(  # Buat objek Plant dari data CSV
                    name=row['name'],
                    #image_url=row['image_url'],
                    overview=row['overview'],
                    tools=row['tools_materials'],
                    harvest=row['harvest_method'],
                    maintenance=row['care_tips'],
                    illness=row['sickness_solution'],
                    small_land_tips=row['limited_land_tip'],
                    harvest_day=row['harvest_day']
                )
                db.session.add(plant)  # Tambahkan ke sesi database
            db.session.commit()  # Simpan semua perubahan

@app.route('/')
def index():
    return render_template('index.html', pompa_status=pompa_status)  # Render halaman utama dengan status pompa

@app.route('/data', methods=['POST'])
def receive_data():
    global sensor_data
    try:
        sensor_data = request.get_json()  # Ambil data JSON dari request
        socketio.emit('update_sensor', sensor_data)  # Kirim data ke klien secara real-time
        return "OK", 200  # Respon sukses
    except Exception as e:
        return f"Error: {str(e)}", 400  # Jika gagal, kirim error 400

@app.route('/pompa', methods=['POST'])
def control_pompa():
    global pompa_status
    action = request.form.get('action', '')  # Ambil aksi dari form (ON/OFF)
    if action in ["ON", "OFF"]:
        pompa_status = action  # Ubah status pompa
        socketio.emit('update_pompa', {"pompa_status": pompa_status})  # Kirim status ke klien
        return '', 204  # Tidak ada konten, tapi sukses
    return 'Invalid Action', 400  # Jika aksi tidak valid

@app.route('/pompa/status', methods=['GET'])
def get_pompa_status():
    return pompa_status, 200  # Kembalikan status pompa saat ini

@app.route('/ML', methods=['POST'])
def predict():
    try:
        data = request.get_json()  # Ambil data JSON dari klien
        print("Data yang diterima untuk prediksi:", data)
        features = [  # Ambil fitur input dan bulatkan ke 1 desimal
            round(data.get('suhu', 0), 1),
            round(data.get('kelembapan_udara', 0), 1),
            round(data.get('hujanV', 0), 1),
            round(data.get('humtanah', 0), 1)
        ]
        input_array = np.array([features])  # Konversi ke array NumPy
        prediction = model.predict(input_array)  # Lakukan prediksi dengan model
        raw_label = prediction[0].lower()  # Ambil hasil prediksi dan ubah ke huruf kecil
        mapped_name = label_mapping.get(raw_label)  # Dapatkan nama tanaman dari mapping

        if not mapped_name:
            return jsonify({'class': raw_label, 'error': 'Tanaman tidak ditemukan dalam mapping'}), 404

        # Cari data tanaman di database
        matched_plant = Plant.query.filter(Plant.name.ilike(mapped_name)).first()
        if matched_plant:
            # Jika ditemukan, kirim detail tanaman sebagai JSON
            return jsonify({
                'class': matched_plant.name,
                #'image_url': matched_plant.image_url,
                'overview': matched_plant.overview,
                'tools': matched_plant.tools,
                'harvest': matched_plant.harvest,
                'maintenance': matched_plant.maintenance,
                'illness': matched_plant.illness,
                'small_land_tips': matched_plant.small_land_tips,
                'harvest_day': matched_plant.harvest_day
            })
        else:
            # Jika tidak ditemukan di database
            return jsonify({'class': mapped_name, 'error': 'Tanaman tidak ditemukan di database'}), 404

    except Exception as e:
        import traceback
        traceback.print_exc()  # Cetak traceback error ke konsol
        print("ERROR DI /ML:", e)
        return jsonify({'error': str(e)}), 500  # Kirim error 500 jika terjadi exception

# Fungsi utama saat server dijalankan
if __name__ == '__main__':
    with app.app_context():  # Aktifkan konteks aplikasi
        create_tables_and_load_data()  # Buat tabel dan isi data dari CSV
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)  # Jalankan server dengan debug aktif
