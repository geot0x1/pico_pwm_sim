from machine import Pin, PWM
import time

MAX_DUTY = 65535

class PWMController:
    def __init__(self):
        self.pwm_pins = {
            17: {'pwm': None, 'freq': 1000, 'dc': 0},
            16: {'pwm': None, 'freq': 1000, 'dc': 0},
        }
        self.input_pins = {
            26: {'pin': None, 'state': 0},
            27: {'pin': None, 'state': 0},
        }
        self.init_pwm()
        self.init_inputs()

    def init_pwm(self):
        for pin_num in self.pwm_pins:
            self.pwm_pins[pin_num]['pwm'] = PWM(Pin(pin_num))
            self.pwm_pins[pin_num]['pwm'].freq(self.pwm_pins[pin_num]['freq'])
            self.set_duty_cycle(pin_num, self.pwm_pins[pin_num]['dc'])

    def init_inputs(self):
        for pin_num in self.input_pins:
            self.input_pins[pin_num]['pin'] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            self.update_input_state(pin_num)

    def update_input_state(self, pin_num):
        self.input_pins[pin_num]['state'] = self.input_pins[pin_num]['pin'].value()

    def set_duty_cycle(self, pin_num, dc):
        if not (0 <= dc <= 100):
            print(f"Error: Duty cycle must be 0-100%, got {dc}")
            return False

        self.pwm_pins[pin_num]['dc'] = dc
        duty_u16 = int(MAX_DUTY * dc / 100)
        self.pwm_pins[pin_num]['pwm'].duty_u16(duty_u16)
        return True

    def set_frequency(self, pin_num, freq):
        if freq <= 0:
            print(f"Error: Frequency must be positive, got {freq}")
            return False

        self.pwm_pins[pin_num]['freq'] = freq
        self.pwm_pins[pin_num]['pwm'].freq(freq)
        return True

    def parse_command(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return

        try:
            if ',' in cmd:
                parts = cmd.split(',')
                if len(parts) != 3:
                    print("Invalid format. Use: p17,freq,dc or p16,freq,dc")
                    return

                pin_str = parts[0].strip().lower()
                freq_str = parts[1].strip()
                dc_str = parts[2].strip()

                if pin_str not in ['p17', 'p16']:
                    print("Invalid pin. Use p17 or p16")
                    return

                pin_num = int(pin_str[1:])
                freq = int(freq_str)
                dc = float(dc_str)

                if self.set_frequency(pin_num, freq):
                    self.set_duty_cycle(pin_num, dc)
                    print(f"PIN{pin_num}: {freq}Hz @ {dc}%")

            elif ' ' in cmd:
                parts = cmd.split()
                pin_str = parts[0].lower()

                if pin_str not in ['p17', 'p16']:
                    print("Invalid pin. Use p17 or p16")
                    return

                pin_num = int(pin_str[1:])

                if len(parts) < 2:
                    print("Incomplete command")
                    return

                param = parts[1].lower()

                if '=' not in param:
                    print("Invalid format. Use: p17 f=1000 or p17 dc=50")
                    return

                key, value = param.split('=', 1)
                value = float(value)

                if key == 'f':
                    if self.set_frequency(pin_num, int(value)):
                        print(f"PIN{pin_num} frequency: {int(value)}Hz (DC: {self.pwm_pins[pin_num]['dc']}%)")
                elif key == 'dc':
                    if self.set_duty_cycle(pin_num, value):
                        print(f"PIN{pin_num} duty cycle: {value}% (Freq: {self.pwm_pins[pin_num]['freq']}Hz)")
                else:
                    print("Unknown parameter. Use 'f' for frequency or 'dc' for duty cycle")

            else:
                print("Invalid format. Examples:")
                print("  p17,1000,50")
                print("  p16 f=2000")
                print("  p17 dc=75")

        except ValueError:
            print("Error: Invalid values. Frequency and duty cycle must be numbers")
        except IndexError:
            print("Error: Invalid command format")

    def status(self):
        print("\n--- PWM Status ---")
        for pin_num in [17, 16]:
            info = self.pwm_pins[pin_num]
            print(f"PIN{pin_num}: {info['freq']}Hz @ {info['dc']}%")
        print("\n--- Input Status ---")
        for pin_num in [26, 27]:
            self.update_input_state(pin_num)
            state = self.input_pins[pin_num]['state']
            state_str = "HIGH" if state else "LOW"
            print(f"PIN{pin_num}: {state_str} (pull-up enabled)")
        print()

    def cleanup(self):
        for pin_num in self.pwm_pins:
            self.pwm_pins[pin_num]['pwm'].duty_u16(0)
            self.pwm_pins[pin_num]['pwm'].deinit()

    def run(self):
        print("PWM Command Controller")
        print("PWM Outputs (PIN17, PIN16):")
        print("  p17,freq,dc          - Set PIN17 frequency and duty cycle")
        print("  p16,freq,dc          - Set PIN16 frequency and duty cycle")
        print("  p17 f=freq           - Set PIN17 frequency only")
        print("  p17 dc=duty          - Set PIN17 duty cycle only")
        print("  p16 f=freq           - Set PIN16 frequency only")
        print("  p16 dc=duty          - Set PIN16 duty cycle only")
        print("\nInputs (PIN26, PIN27 - pull-ups enabled):")
        print("  status               - Show current PWM settings and input states")
        print("\nGeneral:")
        print("  help                 - Show this help message")
        print("  exit                 - Exit program")
        print("-" * 50)

        try:
            while True:
                self.status()
                cmd = input("> ").strip()

                if cmd.lower() in ['exit', 'quit', 'x']:
                    break
                elif cmd.lower() == 'status':
                    continue
                elif cmd.lower() == 'help':
                    print("\nPWM Outputs (PIN17, PIN16):")
                    print("  p17,freq,dc          - Set PIN17 frequency and duty cycle")
                    print("  p16,freq,dc          - Set PIN16 frequency and duty cycle")
                    print("  p17 f=freq           - Set PIN17 frequency only")
                    print("  p17 dc=duty          - Set PIN17 duty cycle only")
                    print("  p16 f=freq           - Set PIN16 frequency only")
                    print("  p16 dc=duty          - Set PIN16 duty cycle only")
                    print("\nInputs (PIN26, PIN27 - pull-ups enabled):")
                    print("  status               - Show current PWM settings and input states")
                    print()
                else:
                    self.parse_command(cmd)

        except KeyboardInterrupt:
            print("\nInterrupted...")
        finally:
            print("Cleaning up...")
            self.cleanup()
            print("Done!")

def main():
    controller = PWMController()
    controller.run()

if __name__ == "__main__":
    main()
