import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

SERVO = 12

SERVO_ABIERTO = 8    
SERVO_CERRADO = 4   

GPIO.setup(SERVO, GPIO.OUT)
pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)

print("\n" + "="*60)
print("TEST DE SERVO ")
print("="*60)
print(f"Posición ABIERTA:  duty {SERVO_ABIERTO}%")
print(f"Posición CERRADA:  duty {SERVO_CERRADO}%\n")

try:
    print("Inicializando servo en posición CERRADA...")
    pwm.ChangeDutyCycle(SERVO_CERRADO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    print("✓ Servo cerrado\n")

    time.sleep(2)

    print("Probando posición ABIERTA...")
    pwm.ChangeDutyCycle(SERVO_ABIERTO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    print("✓ Servo abierto\n")

    time.sleep(2)

    print("Probando posición CERRADA...")
    pwm.ChangeDutyCycle(SERVO_CERRADO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    print("✓ Servo cerrado\n")

    time.sleep(2)

    print("Ciclo completo: CERRADO → ABIERTO → CERRADO")
    pwm.ChangeDutyCycle(SERVO_CERRADO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    time.sleep(1)

    pwm.ChangeDutyCycle(SERVO_ABIERTO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)
    time.sleep(1)

    pwm.ChangeDutyCycle(SERVO_CERRADO)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)


finally:
    pwm.stop()
    GPIO.cleanup()
