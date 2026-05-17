#!/usr/bin/env python3

import paho.mqtt.client as mqtt
import time
from datetime import datetime

# Configuración
BROKER = "localhost"
PUERTO = 1883

# Colores para terminal
COLORES = {
    "RESET": "\033[0m",
    "ROJO": "\033[91m",
    "VERDE": "\033[92m",
    "AMARILLO": "\033[93m",
    "AZUL": "\033[94m",
    "MAGENTA": "\033[95m",
}

def color(texto, color_key):
    """Añade color al texto"""
    return f"{COLORES[color_key]}{texto}{COLORES['RESET']}"

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta"""
    if rc == 0:
        print(color("✓ Conectado al broker MQTT", "VERDE"))
        # Suscribirse a todos los tópicos del sistema
        client.subscribe("casa/incendio/#")
        print(color("✓ Suscrito a: casa/incendio/#\n", "VERDE"))
        print(f"{color('Timestamp', 'AZUL')} | {color('Tópico', 'AZUL')} | {color('Valor', 'AZUL')}")
        print("-" * 80)
    else:
        print(color(f"✗ Error de conexión: {rc}", "ROJO"))

def on_disconnect(client, userdata, rc):
    """Callback cuando se desconecta"""
    if rc != 0:
        print(color(f"✗ Desconexión inesperada: {rc}", "ROJO"))
    else:
        print(color("✓ Desconectado correctamente", "VERDE"))

def on_message(client, userdata, msg):
    """Callback cuando se recibe un mensaje"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    topic = msg.topic
    payload = msg.payload.decode()
    
    # Asignar colores según el tópico
    if "estado" in topic:
        color_valor = "MAGENTA"
    elif "presencia" in topic:
        color_valor = "ROJO" if "Sí" in payload else "VERDE"
    elif "salida_recomendada" in topic:
        color_valor = "AMARILLO"
    else:
        color_valor = "AZUL"
    
    print(f"{color(timestamp, 'AZUL')} | {color(topic, 'VERDE')} | {color(payload, color_valor)}")

def main():
    """Función principal"""
    print("\n" + "="*80)
    print(color("  MONITOR DE MQTT - Sistema de Evacuación de Incendios", "MAGENTA"))
    print("="*80 + "\n")
    
    # Crear cliente MQTT
    client = mqtt.Client(client_id="Monitor_MQTT", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        print(f"Conectando a {BROKER}:{PUERTO}...\n")
        client.connect(BROKER, PUERTO, 60)
        client.loop_forever()
    except ConnectionRefusedError:
        print(color("✗ Error: No se puede conectar al broker.", "ROJO"))
    except KeyboardInterrupt:
        print(f"\n\n{color('Desconectando...', 'AMARILLO')}")
        client.disconnect()

if __name__ == "__main__":
    main()
