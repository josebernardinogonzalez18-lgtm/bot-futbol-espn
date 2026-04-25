import requests
import json
import os

# Configuración de Ligas de Fútbol (URLs de la API de ESPN)
LIGAS = {
    "Premier League": "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
    "Championship": "http://site.api.espn.com/apis/site/v2/sports/soccer/eng.2/scoreboard",
    "La Liga": "http://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
    "Bundesliga": "http://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard"
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "ultimo_estado_futbol.json"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje})
        print(f"Telegram Status: {r.status_code}")
    except Exception as e:
        print(f"Error enviando: {e}")

def cargar_estado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def monitorear():
    print("Iniciando monitoreo de Fútbol...")
    estado_anterior = cargar_estado()
    nuevo_estado = {}

    for liga_nombre, url in LIGAS.items():
        try:
            response = requests.get(url).json()
            eventos = response.get('events', [])
            
            if not eventos:
                continue

            for evento in eventos:
                id_p = evento['id']
                nombre = evento['shortName']
                status_obj = evento['status']['type']
                
                status_desc = status_obj.get('description', "Scheduled")
                # Reloj del partido (ej. 45', 90+2')
                tiempo = evento['status'].get('displayClock', "0'") 
                
                comp = evento['competitions'][0]['competitors']
                # En fútbol internacional el índice 0 suele ser el Local y el 1 el Visitante
                t1, s1 = comp[0]['team']['abbreviation'], comp[0].get('score', "0")
                t2, s2 = comp[1]['team']['abbreviation'], comp[1].get('score', "0")
                marcador = f"{t1} {s1} - {s2} {t2}"

                nuevo_estado[id_p] = {"marcador": marcador, "status": status_desc, "liga": liga_nombre}

                # Lógica de notificaciones
                if id_p in estado_anterior:
                    info_ant = estado_anterior[id_p]
                    status_ant = info_ant.get('status')
                    marcador_ant = info_ant.get('marcador')

                    # 1. ¿Inició el partido? (Pasa de Programado a En Progreso)
                    if status_desc == "In Progress" and status_ant == "Scheduled":
                        enviar_telegram(f"⚽ ¡ARRANCA EL PARTIDO!\n🏆 {liga_nombre}\n🏟️ {nombre}")

                    # 2. ¿Hubo Gol? (Cambia el marcador mientras el partido está activo)
                    elif marcador != marcador_ant and status_desc in ["In Progress", "Halftime", "Extra Time"]:
                        enviar_telegram(f"🚨 ¡GOOOOOOL!\n🏆 {liga_nombre}\n🏟️ {nombre}\n⏱️ Minuto: {tiempo}\n📊 {marcador}")

                    # 3. ¿Llegó al Medio Tiempo?
                    elif status_desc == "Halftime" and status_ant != "Halftime":
                        enviar_telegram(f"⏸️ MEDIO TIEMPO\n🏆 {liga_nombre}\n🏟️ {nombre}\n📊 {marcador}")

                    # 4. ¿Terminó el partido?
                    elif status_desc in ["Full Time", "Final"] and status_ant not in ["Full Time", "Final"]:
                        enviar_telegram(f"🏁 FINAL DEL PARTIDO\n🏆 {liga_nombre}\n🏟️ {nombre}\n📊 Resultado: {marcador}")

                else:
                    # Primera ejecución: Si el juego ya está en vivo, avisar que lo empezamos a seguir
                    if status_desc == "In Progress":
                        enviar_telegram(f"📡 Monitoreando en vivo:\n🏆 {liga_nombre}\n🏟️ {nombre}\n⏱️ {tiempo}\n📊 {marcador}")

        except Exception as e:
            print(f"Error procesando {liga_nombre}: {e}")

    # Guardar el nuevo estado
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(nuevo_estado, f)
        print("Monitoreo completado con éxito.")
    except Exception as e:
        print(f"Error guardando estado: {e}")

if __name__ == "__main__":
    monitorear()
