import requests
import json
import os

# Configuración (Usa variables de entorno por seguridad)
LEAGUE = "mex.1" 
URL = f"http://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE}/scoreboard"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "ultimo_estado.json"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})

def cargar_estado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def guardar_estado(estado):
    with open(STATE_FILE, "w") as f:
        json.dump(estado, f)

def monitorear():
    try:
        response = requests.get(URL).json()
        eventos = response.get('events', [])
        estado_anterior = cargar_estado()
        nuevo_estado = {}

        for evento in eventos:
            id_p = evento['id']
            nombre = evento['shortName']
            status = evento['status']['type']['description']
            home = evento['competitions'][0]['competitors'][0]['team']['shortDisplayName']
            home_s = evento['competitions'][0]['competitors'][0]['score']
            away = evento['competitions'][0]['competitors'][1]['team']['shortDisplayName']
            away_s = evento['competitions'][0]['competitors'][1]['score']
            marcador = f"{home_s}-{away_s}"

            nuevo_estado[id_p] = {"marcador": marcador, "status": status}

            if id_p in estado_anterior:
                # Detectar Gol
                if marcador != estado_anterior[id_p]["marcador"]:
                    enviar_telegram(f"⚽ GOL en {nombre}!\n{home} {home_s} - {away_s} {away}")
                # Detectar Inicio
                if status == "In Progress" and estado_anterior[id_p]["status"] != "In Progress":
                    enviar_telegram(f"▶️ Empezó: {nombre}")
                # Detectar Fin
                if status == "Final" and estado_anterior[id_p]["status"] != "Final":
                    enviar_telegram(f"🏁 Final: {nombre} ({marcador})")
            
        guardar_estado(nuevo_estado)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitorear()
