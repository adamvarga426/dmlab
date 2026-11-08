from flask import Flask
app = Flask(__name__)

import time
import requests
import redis
import json
import os
import datetime
import io
import pandas as pd

from pprint import pprint

redis_host = os.getenv('REDIS_HOST', 'redis_broker')
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)


def fetch_data():
    # Példa külső API hívásra vagy adatgyűjtésre
    # response = requests.get("https://api.example.com/data")
    raw_data = {"title": "Minta Adat", "value": 42.5, "timestamp": time.time()}

    # Küldés a Redis üzenetsorba a feldolgozónak
    r.rpush('raw_data_queue', json.dumps(raw_data))
    print("Adat begyűjtve és elküldve a sorba.")

# def fetch_water_level():


class WaterLevel:
    """Balatoni és egyéb hidrológiai vízszint adatok lekérdezésére és

    feldolgozására szolgáló osztály a hydroinfo.hu archívumából.
    """

    def __init__(self, station_code: str = "442600", years_back: int = 10):
        self.station_code = station_code
        self.current_year = datetime.datetime.now().year
        self.start_year = self.current_year - years_back
        self.df = pd.DataFrame()
        self.month_mapping = {
            "JAN": 1,
            "FEB": 2,
            "MÁR": 3,
            "MAR": 3,
            "ÁPR": 4,
            "APR": 4,
            "MÁJ": 5,
            "MAJ": 5,
            "JÚN": 6,
            "JUN": 6,
            "JÚL": 7,
            "JUL": 7,
            "AUG": 8,
            "SZE": 9,
            "SEP": 9,
            "OKT": 10,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }

    def _get_url(self, year: int) -> str:
        """Meghatározza az adott év megfelelő URL-jét (aktuális vs. archív)."""
        if year == self.current_year:
            return (
                "https://www.hydroinfo.hu/Html/hidinfo/AktualisEvesTb/tb"
                f"{self.station_code}.htm"
            )
        else:
            return (
                f"https://www.hydroinfo.hu/Html/archivum/tb{year}/tb{self.station_code}.htm"
            )

    def _fetch_year_html(self, year: int) -> str:
        """Letölti és kinyeri az HTML táblázatot az adott évre."""
        url = self._get_url(year)
        print(f"Letöltés folyamatban: {year} (URL: {url})")
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = "ISO-8859-2"

            return response.text

        except Exception as e:
            print(f"Hiba történt a(z) {year}. év letöltésekor: {e}")
            return None

    @staticmethod
    def _process_table(raw_year: str, year: int) -> dict:

        processed_year = {}
        response_rows = raw_year.splitlines(True)
        for row in response_rows:
            try:
                remaining_row = row
                day_of_month = int(remaining_row[:6])
                remaining_row = remaining_row[6:]
                for month in range(1, 13):
                    try:
                        d = datetime.date(year, month, day_of_month)
                        # d = f"{year}-{month}-{day_of_month}"
                        processed_year[d] = int(remaining_row[:6])
                    except ValueError:
                        # nem valid adatmező
                        pass
                    finally:
                        remaining_row = remaining_row[6:]

            except ValueError as e:
                # nem adatsor
                continue

        return processed_year

    def fetch_data(self) -> pd.DataFrame:
        """Lekéri az adatokat a megadott időszakra (alapértelmezetten 10 évre visszamenőleg)."""
        water_data = {}
        print(
            f"Vízállás adatgyűjtés indítása a {self.station_code} kódú állomáshoz"
            f" ({self.start_year} – {self.current_year})...\n"
        )

        for year in range(self.start_year, self.current_year + 1):
            raw_year = self._fetch_year_html(year)
            if raw_year is not None:
                water_data |= self._process_table(raw_year, year)

        return water_data


class Weather:
    def __init__(self, years_back: int = 10, latitude: float = 46.9041, longitude: float = 18.0581):
        self.latitude = latitude
        self.longitude = longitude
        self.years_back = years_back
        self.current_year = datetime.datetime.now().year
        self.start_year = self.current_year - years_back
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"

    def fetch_data(self, end_date: str = "2026-11-01") -> dict:
        """
        Lekéri a napi csapadékmennyiséget és napfénytartamot X évre visszamenőleg.

        :param years_back: Hány évre visszamenőleg kérjük le az adatokat.
        :param end_date: A lekérdezés végső dátuma 'YYYY-MM-DD' formátumban.
        :return: Dict a kért struktúrával.
        """
        print()
        print(
            f"Időjárás adatgyűjtés indítása"
            f" ({self.start_year} – {self.current_year})...\n"
        )
        end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

        # Kezdő dátum kiszámítása X évvel korábbra
        try:
            start_date_obj = end_date_obj.replace(year=end_date_obj.year - self.years_back)
        except ValueError:
            # Szökőév február 29 kezelése, ha nem szökőévre esne
            start_date_obj = end_date_obj.replace(year=end_date_obj.year - self.years_back, day=28)

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date_obj.strftime("%Y-%m-%d"),
            "end_date": end_date_obj.strftime("%Y-%m-%d"),
            "daily": "precipitation_sum,sunshine_duration"
        }
        print(f"Letöltés folyamatban url:{self.base_url} - params: {params}")

        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        data = response.json()

        daily_data = data.get("daily", {})
        times = daily_data.get("time", [])
        precipitation = daily_data.get("precipitation_sum", [])
        sunshine = daily_data.get("sunshine_duration", [])

        return self._process_data(times, precipitation, sunshine)

    @staticmethod
    def _process_data(times, precipitation, sunshine):
        result = {}
        for t_str, prec, sun in zip(times, precipitation, sunshine):
            try:
                # A dátum kulcs létrehozása datetime objektumként (vagy date-ként)
                dt_key = datetime.datetime.strptime(t_str, "%Y-%m-%d").date()

                # Az értékek egész számmá konvertálása (kerekítéssel, hiányzó érték esetén 0-val)
                prec_val = int(round(prec)) if prec is not None else 0
                sun_val = int(round(sun)) if sun is not None else 0

                result[dt_key] = {
                    "precipitation": prec_val,
                    "sunshine": sun_val / (60*60)       # másodperc -> óra
                }
            except ValueError as e:
                print(e)
                continue

        return result


@app.route('/api/collect_water_level', methods=['GET'])
def collect_water_level():
    # Példányosítás (10 évre visszamenőleg a Balaton átlag állomással)
    balaton_wl = WaterLevel(station_code="442600", years_back=3)
    # Példányosítás időjárás adatok
    balaton_w = Weather(3)

    # Vízügyi adatok lekérése
    water_result = balaton_wl.fetch_data()

    # Időjárás adatok lekérése
    weather_result = balaton_w.fetch_data()

    # Adatok egybe fésülése
    all_data = {}
    if water_result and weather_result:
        for date_id, water_level in water_result.items():
            weather_for_date = weather_result.get(date_id)
            if weather_for_date:
                all_data[str(date_id)] = weather_for_date | {"water_level": water_level}

    # Adatok részleges kiírása
    i = 0
    for k, v in all_data.items():
        print(f"all data: {type(k)} {k}: {v}")
        if i == 99:
            break
        i += 1

    # Redissel küldjük a processnek DB-be írásra
    r.rpush('all_data_queue', json.dumps(all_data))

    return "collect_water_level"


if __name__ == "__main__":
    print("Collector main")
    app.run(host='0.0.0.0', port=5000, debug=True)



# if __name__ == '__main__':
#     while True:
#         fetch_data()
#         time.sleep(60) # Gyűjtés 60 másodpercenként