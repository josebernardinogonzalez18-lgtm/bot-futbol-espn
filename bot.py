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
    print("Iniciando monitoreo MLB...")
    try:
        response = requests.get(URL).json()
        eventos = response.get('events', [])
        estado_anterior = cargar_estado()
        nuevo_estado = {}

        if not eventos:
            print("No hay eventos.")
            return

        for evento in eventos:
            id_p = evento['id']
            nombre = evento['shortName']
            status_obj = evento['status']['type']
            
            # Usamos .get() para evitar errores si ESPN no envía el dato
            status_desc = status_obj.get('description', "Scheduled")
            detalle = status_obj.get('detail', "TBD")
            
            comp = evento['competitions'][0]['competitors']
            t1, s1 = comp[1]['team']['abbreviation'], comp[1].get('score', "0")
            t2, s2 = comp[0]['team']['abbreviation'], comp[0].get('score', "0")
            marcador = f"{t1} {s1} - {s2} {t2}"

            nuevo_estado[id_p] = {"marcador": marcador, "status": status_desc, "detalle": detalle}

            # Lógica de notificaciones segura
            if id_p not in estado_anterior:
                # Primera vez que vemos el juego: Reportar si ya empezó
                if status_desc == "In Progress":
                    enviar_telegram(f"🏟️ En vivo: {nombre}\nScore: {marcador}\nEstado: {detalle}")
            else:
                info_ant = estado_anterior[id_p]
                
                # 1. ¿Hubo carrera?
                if marcador != info_ant.get('marcador'):
                    enviar_telegram(f"⚾ ¡ANOTACIÓN! {nombre}\nMarcador: {marcador}\n{detalle}")
                
                # 2. ¿Cambió el inning o estado? (Medio tiempo/Cambio de lado)
                elif detalle != info_ant.get('detalle'):
                    enviar_telegram(f"🔄 {nombre}: {detalle}\nMarcador: {marcador}")

                # 3. ¿Terminó el juego?
                if status_desc == "Final" and info_ant.get('status') != "Final":
                    enviar_telegram(f"🏁 FINAL: {nombre}\nResultado: {marcador}")

        with open(STATE_FILE, "w") as f:
            json.dump(nuevo_estado, f)
        print("Monitoreo exitoso.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    monitorear()
