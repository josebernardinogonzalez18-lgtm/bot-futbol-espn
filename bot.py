import requests
import json
import os

# Configuración de Ligas de Fútbol
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
                tiempo = evento['status'].get('displayClock', "0'") 
                
                comp = evento['competitions'][0]['competitors']
                t1, s1 = comp[0]['team']['abbreviation'], comp[0].get('score', "0")
                t2, s2 = comp[1]['team']['abbreviation'], comp[1].get('score', "0")
                marcador = f"{t1} {s1} - {s2} {t2}"

                # Guardamos el estado actual. Si es Final, nos aseguramos de que este sea el marcador definitivo.
                nuevo_estado[id_p] = {"marcador": marcador, "status": status_desc, "liga": liga_nombre}

                # Lógica de notificaciones
                if id_p in estado_anterior:
                    info_ant = estado_anterior[id_p]
                    status_ant = info_ant.get('status')
                    marcador_ant = info_ant.get('marcador')

                    # 1. ¿Inició el partido?
                    if status_desc == "In Progress" and status_ant == "Scheduled":
                        enviar_telegram(f"⚽ ¡ARRANCA EL PARTIDO!\n🏆 {liga_nombre}\n🏟️ {nombre}")

                    # 2. ¿Hubo Gol? (Solo alertar si el partido sigue vivo)
                    elif marcador != marcador_ant and status_desc in ["In Progress", "Halftime", "Extra Time"]:
                        enviar_telegram(f"🚨 ¡GOOOOOOL!\n🏆 {liga_nombre}\n🏟️ {nombre}\n⏱️ Minuto: {tiempo}\n📊 {marcador}")

                    # 3. ¿Llegó al Medio Tiempo?
                    elif status_desc == "Halftime" and status_ant != "Halftime":
                        enviar_telegram(f"⏸️ MEDIO TIEMPO\n🏆 {liga_nombre}\n🏟️ {nombre}\n📊 {marcador}")

                    # 4. ¿Terminó el partido? (Validamos marcador final definitivo)
                    elif status_desc in ["Full Time", "Final", "FT"] and status_ant not in ["Full Time", "Final", "FT"]:
                        # Enviamos la notificación con el marcador ya validado
                        enviar_telegram(f"🏁 FINAL DEL PARTIDO\n🏆 {liga_nombre}\n🏟️ {nombre}\n📊 Resultado Final: {marcador}")

                else:
                    if status_desc == "In Progress":
                        enviar_telegram(f"📡 Monitoreando en vivo:\n🏆 {liga_nombre}\n🏟️ {nombre}\n⏱️ {tiempo}\n📊 {marcador}")

        except Exception as e:
            print(f"Error procesando {liga_nombre}: {e}")

    # Retener en el estado los partidos que ya terminaron hoy para no perder su resultado
    # por si la API de ESPN los saca temporalmente de su respuesta
    for id_p, datos in estado_anterior.items():
        if id_p not in nuevo_estado and datos.get('status') in ["Full Time", "Final", "FT"]:
            nuevo_estado[id_p] = datos

    # Guardar el nuevo estado con los marcadores finales correctos
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(nuevo_estado, f)
        print("Monitoreo completado con éxito y marcadores guardados.")
    except Exception as e:
        print(f"Error guardando estado: {e}")

if __name__ == "__main__":
    monitorear()
