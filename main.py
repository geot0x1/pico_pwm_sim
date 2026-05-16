from machine import Pin, PWM
import time
import _thread

MAX_DUTY = 65535
LED_PIN = 25
BLINK_INTERVAL = 0.5

CHANNEL_A = 17
CHANNEL_B = 16

class PWMController:
    def __init__(self):
        self.pwm_pins = {
            CHANNEL_A: {'pwm': None, 'freq': 1000, 'dc': 0},
            CHANNEL_B: {'pwm': None, 'freq': 1000, 'dc': 0},
        }
        self.led = None
        self.running = True
        self.init_pwm()
        self.init_led()

    def init_pwm(self):
        for pin_num in self.pwm_pins:
            self.pwm_pins[pin_num]['pwm'] = PWM(Pin(pin_num))
            self.pwm_pins[pin_num]['pwm'].freq(self.pwm_pins[pin_num]['freq'])
            self.set_duty_cycle(pin_num, self.pwm_pins[pin_num]['dc'])

    def init_led(self):
        self.led = Pin(LED_PIN, Pin.OUT)
        self.led.off()
        _thread.start_new_thread(self.heartbeat, ())

    def heartbeat(self):
        while self.running:
            self.led.on()
            time.sleep(BLINK_INTERVAL)
            self.led.off()
            time.sleep(BLINK_INTERVAL)

    def set_duty_cycle(self, pin_num, dc):
        if not (0 <= dc <= 100):
            return False
        self.pwm_pins[pin_num]['dc'] = dc
        self.pwm_pins[pin_num]['pwm'].duty_u16(int(MAX_DUTY * dc / 100))
        return True

    def set_frequency(self, pin_num, freq):
        if freq <= 0:
            return False
        self.pwm_pins[pin_num]['freq'] = freq
        self.pwm_pins[pin_num]['pwm'].freq(freq)
        return True

    def set_channel(self, pin_num, freq, dc):
        return self.set_frequency(pin_num, freq) and self.set_duty_cycle(pin_num, dc)

    def parse_command(self, cmd):
        cmd = cmd.strip()
        if not cmd.startswith("SET="):
            return False

        try:
            parts = cmd[4:].split(',')
            mode = int(parts[0])

            if mode == 1:
                if len(parts) != 3:
                    return False
                return self.set_channel(CHANNEL_A, int(parts[1]), int(parts[2]))

            elif mode == 2:
                if len(parts) != 3:
                    return False
                return self.set_channel(CHANNEL_B, int(parts[1]), int(parts[2]))

            elif mode == 3:
                if len(parts) != 5:
                    return False
                ok_a = self.set_channel(CHANNEL_A, int(parts[1]), int(parts[2]))
                ok_b = self.set_channel(CHANNEL_B, int(parts[3]), int(parts[4]))
                return ok_a and ok_b

            return False

        except (ValueError, IndexError):
            return False

    def cleanup(self):
        self.running = False
        time.sleep(0.1)
        if self.led:
            self.led.off()
        for pin_num in self.pwm_pins:
            self.pwm_pins[pin_num]['pwm'].duty_u16(0)
            self.pwm_pins[pin_num]['pwm'].deinit()

    def run(self):
        try:
            while True:
                cmd = input()
                if self.parse_command(cmd):
                    print("OK\r")
                else:
                    print("ERROR\r")
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    Pin(26, Pin.IN, Pin.PULL_UP)
    Pin(27, Pin.IN, Pin.PULL_UP)
    controller = PWMController()
    controller.run()

if __name__ == "__main__":
    main()
