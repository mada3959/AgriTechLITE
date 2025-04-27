from flask import Flask, render_template, Response, request, jsonify, request
import pickle
import numpy as np

app = Flask(__name__)

model = pickle.load(open('models/RandomForest.pkl', 'rb'))

@app.route('/')
def index():
    return render_template('index.html')