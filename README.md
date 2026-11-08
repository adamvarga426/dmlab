# DMLAB Felvételi feladat

## A feladat témája
A balatoni vízállás változásokat és a napsütéses órák és csapadék mennyiség arányát, összefüggéseit szeretném feldolgozni, szemléltetni.

## Rendszerkövetelmények a deployhoz
* Docker
* MySQL adatbázis

## Telepítés
* Hozzunk létre egy MySQL adatbázist.
* Az adatbázis adatait írjuk át a megfelelőre a docker-compose.yml fájlban a mysql_db service-ben és a processor service environment részében egyaránt.
* A projekt gyökerében futtassuk ezt: `docker-compose build --no-cache`
* Adatbázis táblát __nem__ kell létrehozni, ezt a szoftver automatikusan létrehozza / karban tartja az adatgyűjtés folyamán

## Használat
* Sikeres build után indítsuk el az összes konténert: `docker-compose up`
* Böngészőben nyissuk meg: `http://localhost:5000/`
* Első betöltéskor még nem jelennek meg adatok, ill diagram, hiszen az adatbázis nem került felépítsére, az adatok nem lettek összegyűjtva. Ehhez kattintsunk a fenti kék színű gombra.
* Amikor az állapotüzenet megjelenik a gomb alatt, frissítsük a böngészőt, így megjelennek az adatok.

## Adatforrások, paraméterek
* Az utolsó __YEARS_BACK__ számú év napi szintű adatait fetcheljük. Ez a _collector/collector.py_ fájl elején szerkeszthető  
* Vízállás adatok forrása: _https://www.hydroinfo.hu/Html/hidinfo/AktualisEvesTb/tb_
* Időjárás adatok forrása: _https://archive-api.open-meteo.com/v1/archive_

## Architektúra
Az alábbi blokkvázlat szerinti microservice arhitektúrát valósítottam meg python nyelven, Flask keretrendszert, Jinja2 templatea rendszert használva:

[ Gyűjtő (Collector) ] ---> [ Redis ] ---> [ Feldolgozó (Processor + Belső API) ] <--- [ Web / Flask ]
                                                                │
                                                                v
                                                            [ MySQL DB ]

## Tech stack
* Flask
* Jinja2
* SQLAlchemy
* redis
* pandas
* lxml
* threading
* json

