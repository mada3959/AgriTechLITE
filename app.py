from flask import Flask, render_template, Response, request, jsonify
import pickle
import numpy as np

app = Flask(__name__)
model = pickle.load(open('models/RandomForest.pkl', 'rb'))

@app.route('/')
def index():
    return render_template('index.html')

class_names = [
    'Padi', 'Jagung', 'Kacang Arab', 'Kacang Merah', 'Kacang Gude',
    'Kacang Moth', 'Kacang Hijau', 'Kacang Hitam', 'Kacang Lentil', 'Delima',
    'Pisang', 'Mangga', 'Anggur', 'Semangka', 'Melon', 'Apel',
    'Jeruk', 'Pepaya', 'Kelapa', 'Kapas', 'Goni', 'Kopi'
]

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
        predicted_class = class_names[np.argmax(prediction)]
        return jsonify({'class': predicted_class})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
