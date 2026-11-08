import os
import requests
from flask import Flask, render_template, jsonify



app = Flask(__name__)

# A processor mikroszolgáltatás belső címe a Docker hálózaton
PROCESSOR_API_URL = os.getenv('PROCESSOR_API_URL', 'http://processor:5000/api/data')
PROCESSOR_AGGR_API_URL = os.getenv('PROCESSOR_AGGR_API_URL', 'http://processor:5000/api/aggregates')
COLLECTOR_WATER_LEVEL_URL = os.getenv('COLLECTOR_WATER_LEVEL_URL', 'http://collector:5000/api/collect_water_level')


@app.route('/api/collect_trigger')
def collect_trigger():
    # Vízállás adatok összegyűjtése:
    # CORS probléma megoldása
    try:
        print("COLLECTOR_WATER_LEVEL_URL hívása")
        response = requests.get(COLLECTOR_WATER_LEVEL_URL, timeout=3)
        if response.status_code == 200:
            collector_resp = response.text
    except Exception as e:
        print(f"Hiba a collector API elérése közben: {e}")

    return jsonify({}), 200


@app.route('/')
def index():
    data = []
    aggregates = []
    labels = []
    mon_water_level = []
    mon_sunshine = []
    mon_precipitation = []
    try:
        # Lekérdezzük az adatokat a feldolgozó API-tól
        data_response = requests.get(PROCESSOR_API_URL, timeout=3)
        if data_response.status_code == 200:
            data = data_response.json()

        # Aggregált adatok lekérése a feldolgozó API-tól
        aggr_response = requests.get(PROCESSOR_AGGR_API_URL, timeout=3)
        if aggr_response.status_code == 200:
            aggr_data = aggr_response.json()
            aggregates = aggr_data[0]
            labels = aggr_data[1]
            mon_water_level = aggr_data[2]
            mon_sunshine = aggr_data[3]
            mon_precipitation = aggr_data[4]

    except Exception as e:
        print(f"Hiba a processor API elérése közben: {e}")

    return render_template('index.html', data=data, aggregates=aggregates, labels=labels, mon_water_level=mon_water_level, mon_sunshine=mon_sunshine, mon_precipitation=mon_precipitation)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
