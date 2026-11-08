from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Flask alkalmazás indítása a feldolgozóban (csak belső API-ként)
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://mysql_user:mysql_pw@mysql_db:3306/dmlab_db')

db = SQLAlchemy(app)


class DataModel(db.Model):
    __tablename__ = 'weather_water_data'
    date_id = db.Column(db.Date, primary_key=True)
    water_level = db.Column(db.Integer)     # cm
    sunshine = db.Column(db.Integer)        # s
    precipitation = db.Column(db.Integer)   # mm

