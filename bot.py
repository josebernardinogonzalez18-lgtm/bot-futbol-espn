import requests
import json
import os

# Configuración MLB
URL = "http://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "ultimo_estado_mlb.json"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})

def cargar_estado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except: return {}
    return {}

def guardar_estado(estado):
    with open(STATE_FILE, "w") as f:
        json.dump(estado, f)

def monitorear_mlb():
    try:
        response = requests.get(URL).json()
        eventos = response.get('events', [])
        estado_anterior = cargar_estado()
        nuevo_estado = {}

        for evento in eventos:
            id_p = evento['id']
            nombre = evento['shortName'] # Ej: "NYY @ LAD"
            status = evento['status']['type']['description']
            inning = evento['status']['type']['detail'] # Ej: "Top 5th" o "Final"
            
            # Equipos y Carreras (Runs)
            home_team = evento['competitions'][0]['competitors'][0]['team']['abbreviation']
            home_runs = evento['competitions'][0]['competitors'][0]['score']
            away_team = evento['competitions'][0]['competitors'][1]['team']['abbreviation']
            away_runs = evento['competitions'][0]['competitors'][1]['score']
            
            marcador = f"{away_team} {away_runs} - {home_runs} {home_team}"
            nuevo_estado[id_p] = {"marcador": marcador, "status": status}

            if id_p in estado_anterior:
                # 1. Detectar cambio de marcador (Carreras)
                if marcador != estado_anterior[id_p]["marcador"]:
                    enviar_telegram(f"⚾ ¡Cambio en el marcador! ({inning})\n{marcador}")
                
                # 2. Detectar Inicio del juego
                if status == "In Progress" and estado_anterior[id_p]["status"] != "In Progress":
                    enviar_telegram(f"🏟️ ¡Playball! Empieza: {nombre}")
                
                # 3. Detectar Fin del juego
                if status == "Final" and estado_anterior[id_p]["status"] != "Final":
                    enviar_telegram(f"🏁 Juego Terminado: {nombre}\nFinal: {marcador}")
            
        guardar_estado(nuevo_estado)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitorear_mlb()
