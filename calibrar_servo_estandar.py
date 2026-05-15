import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

SERVO_A = 12

GPIO.setup(SERVO_A, GPIO.OUT)
pwm_a = GPIO.PWM(SERVO_A, 50)
pwm_a.start(0)

print("\n" + "="*60)
print("CALIBRADOR DE SERVO ESTÁNDAR M-1504D")
print("="*60)
print("\nEncontrar duty cycle para posiciones abierta y cerrada\n")

def probar_posicion(duty, nombre):
    """Prueba una posición específica del servo"""
    print(f"Probando {nombre} (duty {duty}%)...")
    pwm_a.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm_a.ChangeDutyCycle(0)
    print(f"  ✓ Servo parado en posición {nombre}\n")
    return input("¿Es la posición correcta? (s/n): ").lower() == 's'

try:
    print("="*60)
    print("CALIBRACIÓN POSICIÓN ABIERTA (0°)")
    print("="*60 + "\n")
    print("El servo debe estar en posición para abrir ambas puertas\n")
    
    duty_abierto = None
    for duty in [2, 3, 4, 5, 6, 7]:
        if probar_posicion(duty, "ABIERTA"):
            duty_abierto = duty
            print(f"✓ POSICIÓN ABIERTA: duty {duty_abierto}%\n")
            break
        time.sleep(1)
    
    print("\nEsperando 3 segundos antes de calibrar el cierre...\n")
    time.sleep(3)
    
    print("="*60)
    print("CALIBRACIÓN POSICIÓN CERRADA (180°)")
    print("="*60 + "\n")
    print("El servo debe estar en posición para cerrar ambas puertas\n")
    
    duty_cerrado = None
    for duty in [8, 9, 10, 11, 12]:
        if probar_posicion(duty, "CERRADA"):
            duty_cerrado = duty
            print(f"✓ POSICIÓN CERRADA: duty {duty_cerrado}%\n")
            break
        time.sleep(1)
    
    if duty_abierto and duty_cerrado:
        print("\n" + "="*60)
        print("RESUMEN FINAL")
        print("="*60)
        print(f"Duty cycle ABIERTO:  {duty_abierto}%")
        print(f"Duty cycle CERRADO:  {duty_cerrado}%")
        
        print("\nActualiza estas variables en fase1_led.py:")
        print(f"  SERVO_A_ABIERTO = {duty_abierto}")
        print(f"  SERVO_A_CERRADO = {duty_cerrado}")
        
finally:
    pwm_a.stop()
    GPIO.cleanup()
