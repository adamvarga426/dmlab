FROM python:3.12-slim

# Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# Rendszerszintű függőségek telepítése
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Függőségi fájl másolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alkalmazás kódjának másolása
COPY . .

# Flask környezeti változók
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Port megnyitása
EXPOSE 5000

# Alkalmazás indítása
CMD ["python", "app.py"]