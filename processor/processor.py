import time
import json
import threading
import redis
from flask import jsonify
from models import os, app, db, DataModel
from sqlalchemy import func


# Háttérszál a Redis feldolgozéshez és MySQL mentéshez
def background_processor():
    redis_host = os.getenv('REDIS_HOST', 'redis_broker')
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

    print("Adatfeldolgozó háttérszál elindult...")
    while True:
        try:
            # Kivesszük az adatot a Redis üzenetsorból
            item = r.blpop('all_data_queue', timeout=5)
            if item:
                _init_mysql()
                raw_data = json.loads(item[1])
                with app.app_context():
                    for date_id, w_data in raw_data.items():
                        new_entry = DataModel(
                            date_id=date_id,
                            water_level=w_data.get('water_level'),
                            sunshine=w_data.get('sunshine'),
                            precipitation=w_data.get('precipitation'),
                        )
                        db.session.add(new_entry)
                    db.session.commit()
                print(f"Mentve MySQL-be")
        except Exception as e:
            print(f"Hiba a feldolgozás során: {e}")
        time.sleep(1)


def _init_mysql():
    # MySQL adattábla inicializálása
    try:
        with app.app_context():
            db.drop_all()       # Összes tábla eldobása
            db.create_all()     # Tábla létrehozása
        print("Az adatbázis sikeresen visszaállítva alapállapotba")
    except Exception as e:
        print(f"Hiba az adatbázis inicializálása közben: {str(e)}")


# Adatlekérés web UI részére
@app.route('/api/data', methods=['GET'])
def get_data():
    with app.app_context():
        items = DataModel.query.order_by(DataModel.date_id.asc()).limit(100).all()
        result = [{"date_id": i.date_id.strftime("%Y-%m-%d"),
                   "water_level": i.water_level,
                   "sunshine": i.sunshine,
                   "precipitation": i.precipitation} for i in items]
        return jsonify(result), 200


# Aggregált adatok lekérése web UI részére
@app.route('/api/aggregates', methods=['GET'])
def get_aggregates():
    with app.app_context():
        year_month_col = func.date_format(DataModel.date_id, '%Y-%m').label('year_month')
        result = db.session.query(
            year_month_col,
            func.avg(DataModel.water_level).label('mon_water_level'),
            func.sum(DataModel.sunshine).label('mon_sunshine'),
            func.sum(DataModel.precipitation).label('mon_precipitation')
        ).group_by(year_month_col).order_by(year_month_col).all()

        aggr_data = []
        for row in result:
            aggr_data.append({
                'year_month': row.year_month,
                'mon_water_level': row.mon_water_level,
                'mon_sunshine': row.mon_sunshine,
                'mon_precipitation': row.mon_precipitation,
            })

        labels = [row.year_month for row in result]
        mon_water_level = [row.mon_water_level for row in result]
        mon_sunshine = [row.mon_sunshine for row in result]
        mon_precipitation = [row.mon_precipitation for row in result]


        return jsonify([aggr_data, labels, mon_water_level, mon_sunshine, mon_precipitation])


if __name__ == '__main__':
    # Elindítjuk a háttérfeldolgozót egy külön szálon
    t = threading.Thread(target=background_processor, daemon=True)
    t.start()

    # Elindítjuk a Flask API szervert az 5000-es porton
    app.run(host='0.0.0.0', port=5000, debug=True)
