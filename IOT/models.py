from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    #image_url = db.Column(db.String(255))
    overview = db.Column(db.Text)
    tools = db.Column(db.Text)
    harvest = db.Column(db.Text)
    maintenance = db.Column(db.Text)
    illness = db.Column(db.Text)
    small_land_tips = db.Column(db.Text)
    harvest_day = db.Column(db.String(50))
