import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

SERVO = 12
GPIO.setup(SERVO, GPIO.OUT)

pwm = GPIO.PWM(SERVO, 50)
pwm.start(0)

def mover_servo(pos):
    pwm.ChangeDutyCycle(pos)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)

try:
    while True:
        print("Abierto")
        mover_servo(3)
        time.sleep(2)

        print("Cerrado")
        mover_servo(6)
        time.sleep(2)

except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()