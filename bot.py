import requests
import json
import os

# Configuración
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
        print(f"Error Telegram: {e}")

def cargar_estado():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def monitorear():
    # Mensaje de vida para saber que el script corrió
    print("Iniciando monitoreo MLB...")
    
    try:
        response = requests.get(URL).json()
        eventos = response.get('events', [])
        estado_anterior = cargar_estado()
        nuevo_estado = {}

        if not eventos:
            enviar_telegram("⚠️ El bot corrió pero no encontró partidos programados para hoy en ESPN.")
            return

        for evento in eventos:
            id_p = evento['id']
            nombre = evento['shortName']
            status_obj = evento['status']['type']
            status_desc = status_obj['description'] # Scheduled, In Progress, Final
            detalle = status_obj.get('detail', "") # "Top 3rd", "Mid 4th", "Final"
            
            # Marcador
            comp = evento['competitions'][0]['competitors']
            t1, s1 = comp[1]['team']['abbreviation'], comp[1].get('score', "0")
            t2, s2 = comp[0]['team']['abbreviation'], comp[0].get('score', "0")
            marcador = f"{t1} {s1} - {s2} {t2}"

            nuevo_estado[id_p] = {"marcador": marcador, "status": status_desc, "detalle": detalle}

            # --- LÓGICA DE ENVÍO ---
            if id_p not in estado_anterior:
                # Si el juego ya empezó, avisar de inmediato quién va ganando
                if status_desc == "In Progress":
                    enviar_telegram(f"📡 CONECTADO: {nombre}\nEstado: {detalle}\nMarcador: {marcador}")
            else:
                # 1. Cambio de marcador (Carreras)
                if marcador != estado_anterior[id_p]["marcador"]:
                    enviar_telegram(f"⚾ ¡ANOTACIÓN en {nombre}!\nMarcador: {marcador}\nMomento: {detalle}")
                
                # 2. Cambio de Inning (Medio tiempo / Cambio de lado)
                # Detecta cuando el detalle cambia (ej. de Top a Mid o de Mid a Bottom)
                if detalle != estado_anterior[id_p]["detalle"]:
                    enviar_telegram(f"🔄 Actualización {nombre}: {detalle}\nMarcador: {marcador}")

                # 3. Final del partido
                if status_desc == "Final" and estado_anterior[id_p]["status"] != "Final":
                    enviar_telegram(f"🏁 JUEGO TERMINADO: {nombre}\nFinal: {marcador}")

        with open(STATE_FILE, "w") as f:
            json.dump(nuevo_estado, f)
            
    except Exception as e:
        print(f"Error: {e}")
        enviar_telegram(f"❌ Error en el bot: {str(e)}")

if __name__ == "__main__":
    monitorear()
