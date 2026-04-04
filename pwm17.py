from machine import Pin, PWM
from utime import sleep

pwm = PWM(Pin(17))
pwm.freq(1000)

while True:
    try:
        for duty in range(0, 65536, 1000):
            pwm.duty_u16(duty)
            sleep(0.01)
        for duty in range(65535, -1000, -1000):
            pwm.duty_u16(duty)
            sleep(0.01)
    except KeyboardInterrupt:
        break

pwm.duty_u16(0)
pwm.deinit()
print("Finished.")