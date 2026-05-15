import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

SERVO = 12  # Cambia a 13 para probar SERVO_B

GPIO.setup(SERVO, GPIO.OUT)
pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)

print("\n" + "="*50)
print("CALIBRADOR DE SERVO SG90")
print("="*50)
print("\nPrueba diferentes valores de duty cycle")
print("Observa en qué posición queda el servo\n")

try:
    while True:
        duty = input("Ingresa duty cycle (2-12, o 'q' para salir): ")
        
        if duty.lower() == 'q':
            break
            
        try:
            duty_value = float(duty)
            if 2 <= duty_value <= 12:
                print(f"Moviendo a duty cycle: {duty_value}%")
                pwm.ChangeDutyCycle(duty_value)
                time.sleep(0.5)
                
                # Mostrar equivalente en ms
                ms = (duty_value / 100) * 20  # 20ms = 1 período a 50Hz
                print(f"  Equivalente: {ms:.2f}ms")
                print(f"  Ángulo aproximado: {(ms - 1.0) / (2.0 - 1.0) * 180:.0f}°\n")
            else:
                print("El valor debe estar entre 2 y 12\n")
        except ValueError:
            print("Ingresa un número válido\n")
            
finally:
    print("\nPosiciones recomendadas para SG90:")
    print("  5% duty  (1.0ms)  = 0°   (ABIERTO)")
    print("  7.5% duty (1.5ms) = 90°  (CENTRO)")
    print("  10% duty (2.0ms) = 180° (CERRADO)")
    print("\nSi tu servo no coincide con estos valores,")
    print("anota los valores correctos para tu servo específico\n")
    
    pwm.stop()
    GPIO.cleanup()
