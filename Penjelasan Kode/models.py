from flask_sqlalchemy import SQLAlchemy  # Mengimpor SQLAlchemy dari Flask untuk digunakan sebagai ORM (Object Relational Mapper)

db = SQLAlchemy()  # Membuat instance SQLAlchemy yang akan digunakan untuk menghubungkan model ke database

# Mendefinisikan model 'Plant' yang merepresentasikan tabel 'plant' di database
class Plant(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  # Kolom 'id' bertipe Integer dan menjadi primary key (unik untuk setiap entri)
    name = db.Column(db.String(100))  # Kolom 'name' bertipe string dengan maksimal 100 karakter, menyimpan nama tanaman
    #image_url = db.Column(db.String(255))  # Kolom 'image_url' menyimpan URL gambar tanaman (maks 255 karakter)
    overview = db.Column(db.Text)  # Kolom 'overview' menyimpan deskripsi umum atau ringkasan tentang tanaman
    tools = db.Column(db.Text)  # Kolom 'tools' menyimpan daftar alat atau bahan yang diperlukan untuk menanam tanaman
    harvest = db.Column(db.Text)  # Kolom 'harvest' menyimpan informasi cara panen tanaman tersebut
    maintenance = db.Column(db.Text)  # Kolom 'maintenance' menyimpan cara merawat atau menjaga tanaman
    illness = db.Column(db.Text)  # Kolom 'illness' menyimpan penanganan jika tanaman sakit (penyakit dan solusinya)
    small_land_tips = db.Column(db.Text)  # Kolom 'small_land_tips' menyimpan tips menanam di lahan terbatas
    harvest_day = db.Column(db.String(50))  # Kolom 'harvest_day' menyimpan estimasi waktu panen, contoh: "90-120 hari"
