import RPi.GPIO as GPIO
import time
from RPLCD.i2c import CharLCD
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ===== CONFIGURACION GPIO =====
LED_ROJO_A = 27      # Peligro zona A
LED_ROJO_B = 17      # Peligro zona B
LED_VERDE_A = 23     # Salida A segura
LED_VERDE_B = 22     # Salida B segura

BOTON_A = 5          # Emergencia zona A
BOTON_B = 6          # Emergencia zona B

BUZZER = 25

# ===== CONFIGURACION SERVO =====
SERVO = 12         # Servo para ambas salidas

# Tipo de servo: "standar" o "continuo"
TIPO_SERVO = "standar"  # Servo estándar M-1504D

SERVO_ABIERTO = 8    # Posición para abrir ambas puertas
SERVO_CERRADO = 4   # Posición para cerrar ambas puertas

# LCD
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16,
    rows=2
)

# Ultrasonidos (sensor de presencia)
TRIG = 18
ECHO = 24

# Configuracion LEDs
GPIO.setup(LED_ROJO_A, GPIO.OUT)
GPIO.setup(LED_ROJO_B, GPIO.OUT)
GPIO.setup(LED_VERDE_A, GPIO.OUT)
GPIO.setup(LED_VERDE_B, GPIO.OUT)

# Configuracion botones con pull-up interno
GPIO.setup(BOTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BOTON_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Configuracion buzzer
GPIO.setup(BUZZER, GPIO.OUT)

# Configuracion servo
GPIO.setup(SERVO, GPIO.OUT)
pwm = GPIO.PWM(SERVO, 50)  # 50Hz
pwm.start(0)

# Configuracion ultrasonidos
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ===== CONFIGURACION MQTT =====
BROKER = "localhost"
PUERTO = 1883
KEEPALIVE = 60

# Topics MQTT organizados por jerarquía
TOPICS = {
    "estado": "casa/incendio/estado",           # NORMAL, A, B
    "distancia": "casa/incendio/sensor/distancia",
    "presencia": "casa/incendio/sensor/presencia",
    "salida_recomendada": "casa/incendio/salida_recomendada",
    "buzzer": "casa/incendio/buzzer",
    "comando": "casa/incendio/comando"
}

# Variables globales
estado = "NORMAL"
ultimo_estado = None
persona_detectada = False
ultimo_envio_mqtt = 0
mqtt_conectado = False

# ===== CALLBACKS MQTT =====
def on_connect(client, userdata, flags, rc):
    """Callback ejecutado cuando el cliente se conecta al broker"""
    global mqtt_conectado
    if rc == 0:
        print("[MQTT] Conexión exitosa al broker")
        mqtt_conectado = True
        client.subscribe(TOPICS["comando"])
        print(f"[MQTT] Suscrito a: {TOPICS['comando']}")
    else:
        print(f"[MQTT] Error de conexión, código: {rc}")
        mqtt_conectado = False

def on_disconnect(client, userdata, rc):
    """Callback ejecutado cuando el cliente se desconecta"""
    global mqtt_conectado
    mqtt_conectado = False
    if rc != 0:
        print(f"[MQTT] Desconexión inesperada, código: {rc}")

def on_publish(client, userdata, mid):
    """Callback ejecutado cuando se publica un mensaje"""
    pass  

def on_message(client, userdata, msg):
    """Callback ejecutado cuando se recibe un mensaje en un tópico suscrito"""
    global estado
    if msg.topic == TOPICS["comando"]:
        comando = msg.payload.decode()
        print(f"[MQTT] Comando recibido: {comando}")

# Crear cliente MQTT
client = mqtt.Client(client_id="RaspberryPI_Casa", protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_message = on_message

# Conectarse al broker
try:
    print(f"[MQTT] Conectando a {BROKER}:{PUERTO}...")
    client.connect(BROKER, PUERTO, KEEPALIVE)
    client.loop_start()  # Inicia el bucle de red en background
except Exception as e:
    print(f"[MQTT] Error al conectar: {e}")


# ===== FUNCIONES MQTT =====
def publicar_mqtt(tema, valor):
    """Publica un mensaje en MQTT de forma segura"""
    if mqtt_conectado:
        try:
            result = client.publish(tema, str(valor), qos=1)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] Error al publicar en {tema}: {result.rc}")
        except Exception as e:
            print(f"[MQTT] Excepción al publicar: {e}")
    else:
        print(f"[MQTT] No conectado. No se publica {tema}")

def publicar_estado_completo(distancia, persona, salida_recomendada, buzzer_activo):
    """Publica todos los sensores y estados al broker (Publish step 3)"""
    # PUBLISH: Estado del sistema
    publicar_mqtt(TOPICS["estado"], estado)
    
    # PUBLISH: Datos del sensor ultrasonido
    publicar_mqtt(TOPICS["distancia"], round(distancia, 2))
    publicar_mqtt(TOPICS["presencia"], "Sí" if persona else "No")
    
    # PUBLISH: Salida recomendada
    publicar_mqtt(TOPICS["salida_recomendada"], salida_recomendada)
    
    # PUBLISH: Estado del buzzer
    buzzer_estado = "Activado" if buzzer_activo else "Desactivado"
    publicar_mqtt(TOPICS["buzzer"], buzzer_estado)

def medir_distancia():
    GPIO.output(TRIG, False)
    time.sleep(0.05)

    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    inicio = time.time()
    timeout = inicio + 0.02

    while GPIO.input(ECHO) == 0:
        inicio = time.time()
        if inicio > timeout:
            return 999

    final = time.time()
    timeout = final + 0.02

    while GPIO.input(ECHO) == 1:
        final = time.time()
        if final > timeout:
            return 999

    duracion = final - inicio
    distancia = duracion * 34300 / 2

    return distancia

def apagar_todo():
    GPIO.output(LED_ROJO_A, GPIO.LOW)
    GPIO.output(LED_ROJO_B, GPIO.LOW)
    GPIO.output(LED_VERDE_A, GPIO.LOW)
    GPIO.output(LED_VERDE_B, GPIO.LOW)
    GPIO.output(BUZZER, GPIO.LOW)

def mover_servo(accion):
    """Mueve el servo único que controla ambas puertas
    
    """
    if TIPO_SERVO == "continuo":
        if accion == "abierto":
            pwm.ChangeDutyCycle(5)
            time.sleep(TIEMPO_SERVO_ABIERTO)
            pwm.ChangeDutyCycle(0)
        elif accion == "cerrado":
            pwm.ChangeDutyCycle(10)
            time.sleep(TIEMPO_SERVO_CERRADO)
            pwm.ChangeDutyCycle(0)
    else:  # servo standar
        duty = SERVO_ABIERTO if accion == "abierto" else SERVO_CERRADO
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        pwm.ChangeDutyCycle(0)

def inicializar_servo():
    """Inicializa el servo en posición CERRADA al arrancar"""
    print("[SISTEMA] Inicializando servo en posición CERRADA...")
    puerta_cerrada()
    print("[SISTEMA] Servo listo")

def modo_normal():
    apagar_todo()
    GPIO.output(BUZZER, False)
    puerta_abierta()
    
def puerta_abierta():
    """Abre ambas puertas con el servo único"""
    mover_servo("abierto")

def puerta_cerrada():
    """Cierra ambas puertas con el servo único"""
    mover_servo("cerrado")
    
def mensaje_lcd(linea1, linea2=""):
    lcd.clear()
    lcd.write_string(linea1[:16])
    lcd.crlf()
    lcd.write_string(linea2[:16])
    
def hay_persona():
    distancia = medir_distancia()
    return distancia < 10

def alarma_buzzer():
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.2)
    GPIO.output(BUZZER, GPIO.LOW)
    time.sleep(0.2)

def aplicar_estado(persona):
    """Aplica el estado actual del sistema y actualiza salida recomendada
    
    Args:
        persona (bool): Si se detecta persona en el sensor
    
    Returns:
        str: Salida recomendada (A, B, o "N/A")
    """
    apagar_todo()
    salida_recomendada = "N/A"

    if estado == "NORMAL":
        puerta_abierta()  # Abre ambas puertas
        mensaje_lcd("SISTEMA ACTIVO", "Sin emergencia")
        print("[SISTEMA] Estado: NORMAL - Sistema funcionando")
        salida_recomendada = "N/A"

    elif estado == "A":
        GPIO.output(LED_ROJO_A, GPIO.HIGH)     # Zona A peligrosa
        
        if persona:
            # Persona detectada en zona A peligrosa -> usar salida B
            GPIO.output(LED_VERDE_B, GPIO.HIGH)
            puerta_abierta() 
            mensaje_lcd("ALERTA INCENDIO!", "Evacuar por SALIDA B")
            print("[EMERGENCIA] Zona A: PERSONA DETECTADA -> Usar Salida B")
            salida_recomendada = "B"
        else:
            # No hay personas, cerrar puertas por seguridad
            puerta_cerrada()
            mensaje_lcd("Zona A peligro", "Sin personas actualmente")
            print("[ALERTA] Zona A: Incendio detectado, sin personas por ahora")
            salida_recomendada = "N/A"

    elif estado == "B":
        GPIO.output(LED_ROJO_B, GPIO.HIGH)     # Zona B peligrosa
        
        if persona:
            # Persona detectada en zona B peligrosa -> usar salida A
            GPIO.output(LED_VERDE_A, GPIO.HIGH)
            puerta_abierta() 
            mensaje_lcd("ALERTA INCENDIO!", "Evacuar por SALIDA A")
            print("[EMERGENCIA] Zona B: PERSONA DETECTADA -> Usar Salida A")
            salida_recomendada = "A"
        else:
            # No hay personas, cerrar puertas por seguridad
            puerta_cerrada()
            mensaje_lcd("Zona B peligro", "Sin personas actualmente")
            print("[ALERTA] Zona B: Incendio detectado, sin personas por ahora")
            salida_recomendada = "N/A"

    return salida_recomendada



try:
    print("\n" + "="*50)
    print("SISTEMA DE EVACUACION DE INCENDIOS INICIADO")
    print("="*50 + "\n")
    
    # Inicializar servos en posición cerrada
    inicializar_servo()
    
    salida_recomendada = "N/A"
    ultimo_estado = estado
    persona_anterior = None
    buzzer_activo = False
    distancia_actual = 0

    while True:
        # ===== LECTURA DE SENSORES =====
        distancia_actual = medir_distancia()
        
        # SUBSCRIBE: Interpretar datos del sensor (paso 2)
        if distancia_actual < 10:
            persona_detectada = True
        else:
            persona_detectada = False
        
        # ===== DETECCION DE BOTONES =====
        if GPIO.input(BOTON_A) == GPIO.LOW:
            if estado == "A":
                estado = "NORMAL"
                print("\n[BOTON A] Presionado - Cancelando emergencia A")
            else:
                estado = "A"
                print("\n[BOTON A] Presionado - Emergencia en ZONA A")
            time.sleep(0.3)  # Debounce

        if GPIO.input(BOTON_B) == GPIO.LOW:
            if estado == "B":
                estado = "NORMAL"
                print("\n[BOTON B] Presionado - Cancelando emergencia B")
            else:
                estado = "B"
                print("\n[BOTON B] Presionado - Emergencia en ZONA B")
            time.sleep(0.3)  # Debounce
        
        # ===== APLICAR CAMBIOS DE ESTADO =====
        if estado != ultimo_estado or persona_detectada != persona_anterior:
            salida_recomendada = aplicar_estado(persona_detectada)
            ultimo_estado = estado
            persona_anterior = persona_detectada
        
        # ===== ACTIVAR ALARMA SI NECESARIO =====
        if estado in ["A", "B"] and persona_detectada:
            buzzer_activo = True
            alarma_buzzer()
        else:
            if buzzer_activo:
                buzzer_activo = False
            GPIO.output(BUZZER, GPIO.LOW)
        
        # ===== PUBLICAR EN MQTT (cada 1 segundo) =====
        if time.time() - ultimo_envio_mqtt > 1.0:
            publicar_estado_completo(distancia_actual, persona_detectada, salida_recomendada, buzzer_activo)
            ultimo_envio_mqtt = time.time()
        
        time.sleep(0.05)  # Loop cada 50ms para responsive buttons


except KeyboardInterrupt:
    print("\n\n" + "="*50)
    print("APAGANDO SISTEMA...")
    print("="*50)
    apagar_todo()
    # El servo se detiene automáticamente
    pwm.stop()
    lcd.clear()
    client.loop_stop()
    client.disconnect()
    GPIO.cleanup()
    print("Sistema apagado correctamente.\n")