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
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
        print(f"Respuesta Telegram: {r.status_code}")
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

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
    print("Consultando API de ESPN...")
    try:
        response = requests.get(URL).json()
        eventos = response.get('events', [])
        estado_anterior = cargar_estado()
        nuevo_estado = {}

        if not eventos:
            print("No hay eventos programados para hoy.")
            return

        for evento in eventos:
            id_p = evento['id']
            nombre = evento['shortName']
            status_obj = evento['status']['type']
            status_desc = status_obj['description'] # "In Progress", "Final", "Scheduled"
            inning = status_obj.get('detail', "TBD")
            
            # Extraer equipos y carreras
            competitors = evento['competitions'][0]['competitors']
            # ESPN suele poner al visitante en index 1 y local en 0
            team1 = competitors[0]['team']['abbreviation']
            score1 = competitors[0].get('score', "0")
            team2 = competitors[1]['team']['abbreviation']
            score2 = competitors[1].get('score', "0")
            
            marcador = f"{team2} {score2} - {score1} {team1}" # Formato estándar Visita-Local
            nuevo_estado[id_p] = {"marcador": marcador, "status": status_desc}

            # LÓGICA DE NOTIFICACIÓN
            if id_p not in estado_anterior:
                # Si es un partido nuevo y ya empezó, avisar
                if status_desc == "In Progress":
                    enviar_telegram(f"⚾ Seguimiento iniciado: {nombre}\nMarcador actual: {marcador} ({inning})")
                elif status_desc == "Scheduled":
                    print(f"Partido programado: {nombre}")
            else:
                # 1. Detectar cambio de marcador
                if marcador != estado_anterior[id_p]["marcador"]:
                    enviar_telegram(f"🔥 ¡CARRERA en {nombre}!\nScore: {marcador}\nMomento: {inning}")
                
                # 2. Detectar inicio
                if status_desc == "In Progress" and estado_anterior[id_p]["status"] != "In Progress":
                    enviar_telegram(f"🏟️ ¡Playball! Empieza: {nombre}")
                
                # 3. Detectar fin
                if status_desc == "Final" and estado_anterior[id_p]["status"] != "Final":
                    enviar_telegram(f"🏁 Juego Terminado: {nombre}\nResultado Final: {marcador}")
            
        guardar_estado(nuevo_estado)
        print("Proceso completado con éxito.")
    except Exception as e:
        print(f"Error general: {e}")

if __name__ == "__main__":
    monitorear_mlb()
