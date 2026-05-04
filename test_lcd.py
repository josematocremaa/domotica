from RPLCD.i2c import CharLCD
import time

lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x27,
    port=1,
    cols=16,
    rows=2
)

lcd.clear()
lcd.write_string("Sistema OK")
lcd.crlf()
lcd.write_string("LCD funciona")

time.sleep(5)
lcd.clear()