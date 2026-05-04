import RPi.GPIO as GPIO
import time
from RPLCD.i2c import CharLCD
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

LED_ROJO_A = 17      # Peligro zona A
LED_ROJO_B = 27      # Peligro zona B
LED_VERDE_A = 22     # Salida A segura
LED_VERDE_B = 23     # Salida B segura


BOTON_A = 5          # Emergencia zona A
BOTON_B = 6          # Emergencia zona B

BUZZER = 25

SERVO=12

# LCD
lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16,
    rows=2
)

#ultrasonidos
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

#configuracion buzzer
GPIO.setup(BUZZER, GPIO.OUT)

#configuracion servo
GPIO.setup(SERVO, GPIO.OUT)

pwm = GPIO.PWM(SERVO, 50)  # 50Hz
pwm.start(0)

#configuracion ultrasonidos
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

BROKER = "localhost"
client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.loop_start()

estado = "NORMAL"
ultimo_estado = None

def publicar_mqtt(distancia, persona):
    client.publish("casa/estado", estado)
    client.publish("casa/distancia", round(distancia, 2))
    client.publish("casa/presencia", str(persona))

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
    
def modo_normal():
    apagar_todo()
    GPIO.output(BUZZER, False)
    puerta_abierta()
    
def mover_servo(duty):
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)


def puerta_abierta():
    mover_servo(2)


def puerta_cerrada():
    mover_servo(7)
    
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

def aplicar_estado():
    apagar_todo()
    persona = hay_persona()

    if estado == "NORMAL":
        puerta_abierta()
        mensaje_lcd("SISTEMA ACTIVO", "Sin emergencia")
        print("Sistema normal")

    elif estado == "A":
        GPIO.output(LED_ROJO_A, GPIO.HIGH)     # Zona A peligrosa
        
        if persona:
            GPIO.output(LED_VERDE_B, GPIO.HIGH)    #usar salida B
            puerta_cerrada()
            mensaje_lcd("ALERTA INCENDIO Zona A", "Evacuar por B")
            print("Persona detectada. Incendio A -> usar salida B")
        else:
            mensaje_lcd("Zona A peligro", "Sin personas")
            print("Incendio A detectado, pero no hay personas")

    elif estado == "B":
        GPIO.output(LED_ROJO_B, GPIO.HIGH)     # Zona B peligrosa
        
        if persona:
            GPIO.output(LED_VERDE_A, GPIO.HIGH)   #usar salida A
            puerta_cerrada()
            mensaje_lcd("ALERTA INCENDIO Zona B", "Evacuar por A")
            print("Persona detectada. Incendio B -> usar salida A")
        else:
            mensaje_lcd("Zona B peligro", "Sin personas")
            print("Incendio B detectado, pero no hay personas")


try:
    aplicar_estado()
    ultimo_estado = estado
    ultimo_envio = 0

    while True:
        
        distancia = medir_distancia()

        if distancia < 10:
            persona_detectada = True
        else:
            persona_detectada = False
        
        publicar_mqtt(distancia, persona_detectada)
        
        if time.time() - ultimo_envio > 2:  # cada 1 segundo
            publicar_mqtt(distancia, persona_detectada)
            ultimo_envio = time.time()
        
        if GPIO.input(BOTON_A) == GPIO.LOW:
            if estado == "A":
                estado = "NORMAL"
            else:
                estado = "A"
            time.sleep(0.2)

        if GPIO.input(BOTON_B) == GPIO.LOW:
            if estado == "B":
                estado = "NORMAL"
            else:
                estado = "B"
            time.sleep(0.2)

        if estado != ultimo_estado:
            aplicar_estado()
            ultimo_estado = estado
            
        if estado in ["A", "B"] and persona_detectada:  #ALARMA SI HAY PERSONAS
            alarma_buzzer()
        else:
            GPIO.output(BUZZER, GPIO.LOW)

        time.sleep(0.05)


except KeyboardInterrupt:
    print("Apagando sistema...")
    apagar_todo()
    puerta_abierta()
    pwm.stop()
    lcd.clear()
    GPIO.cleanup()