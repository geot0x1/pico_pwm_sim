from machine import Pin, PWM
import time

PIN = 17
MAX_DUTY = 65535

class PWMMode:
    def get_params(self):
        raise NotImplementedError
    
    def run(self, freq=None, dc=None, step=None, delay=None):
        raise NotImplementedError
    
    def cleanup(self, pwm):
        pwm.duty_u16(0)
        pwm.deinit()


class FixedMode(PWMMode):
    def get_params(self):
        print("\n=== Fixed Frequency and Duty Cycle ===")
        try:
            freq = int(input("Enter frequency (Hz): "))
            dc = float(input("Enter duty cycle (%): "))
            if dc < 0 or dc > 100:
                print("Duty cycle must be between 0 and 100")
                return None, None, None, None
            return freq, dc, None, None
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return None, None, None, None

    def run(self, freq=None, dc=None, step=None, delay=None):
        pwm = PWM(Pin(PIN))
        pwm.freq(freq)
        duty_u16 = int(MAX_DUTY * dc / 100)
        pwm.duty_u16(duty_u16)
        
        print(f"\nRunning PWM: {freq}Hz at {dc}% duty cycle")
        print("Press Ctrl+C to go back to menu")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        
        self.cleanup(pwm)


class MovingDCMode(PWMMode):
    def get_params(self):
        print("\n=== Fixed Freq, Moving DC ===")
        try:
            freq = int(input("Enter frequency (Hz): "))
            dc_step = float(input("Enter DC step per iteration (%): "))
            delay_ms = float(input("Enter delay per step (ms): "))
            if dc_step <= 0 or delay_ms <= 0:
                print("Step and delay must be positive")
                return None, None, None, None
            return freq, None, dc_step, delay_ms
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return None, None, None, None

    def run(self, freq=None, dc=None, step=None, delay=None):
        pwm = PWM(Pin(PIN))
        pwm.freq(freq)
        
        duty = 0
        direction = 1
        step_u16 = int(MAX_DUTY * step / 100)
        
        print(f"\nRunning PWM: {freq}Hz, DC step: {step}%, delay: {delay}ms")
        print("Press Ctrl+C to go back to menu")
        
        try:
            while True:
                pwm.duty_u16(duty)
                current_dc = int(duty / MAX_DUTY * 100)
                print(f"Duty cycle: {current_dc}%")
                time.sleep_ms(int(delay))
                duty += step_u16 * direction
                if duty >= MAX_DUTY:
                    direction = -1
                elif duty <= 0:
                    direction = 1
        except KeyboardInterrupt:
            print("\nStopping...")
        
        self.cleanup(pwm)


class InteractiveMode(PWMMode):
    FREQ_STEP = 10
    DC_STEP = 1
    
    def get_params(self):
        print("\n=== Interactive Mode ===")
        print("Controls: UP/DOWN=freq, LEFT/RIGHT=dc, F<num>=freq, DC<num>=dc, x=exit")
        try:
            freq = int(input("Enter starting frequency (Hz): "))
            dc = float(input("Enter starting duty cycle (%): "))
            if dc < 0 or dc > 100:
                print("Duty cycle must be between 0 and 100")
                return None, None, None, None
            return freq, dc, None, None
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return None, None, None, None

    def run(self, freq=None, dc=None, step=None, delay=None):
        pwm = PWM(Pin(PIN))
        pwm.freq(freq)
        duty_u16 = int(MAX_DUTY * dc / 100)
        pwm.duty_u16(duty_u16)
        
        print(f"\nInteractive Mode: {freq}Hz at {dc}%")
        print("Arrow keys: UP/DOWN=freq, LEFT/RIGHT=dc, F<num>=freq, DC<num>=dc, x: exit")
        
        try:
            while True:
                print(f"Freq: {freq}Hz, DC: {int(dc)}%")
                cmd = input("> ")
                if not cmd:
                    continue
                cmd = cmd.strip()
                
                # Check for arrow keys (escape sequences)
                if cmd.startswith('\x1b'):
                    if 'A' in cmd:  # UP
                        freq += self.FREQ_STEP
                        pwm.freq(freq)
                    elif 'B' in cmd:  # DOWN
                        freq = max(1, freq - self.FREQ_STEP)
                        pwm.freq(freq)
                    elif 'C' in cmd:  # RIGHT
                        dc = min(100, dc + self.DC_STEP)
                        pwm.duty_u16(int(MAX_DUTY * dc / 100))
                    elif 'D' in cmd:  # LEFT
                        dc = max(0, dc - self.DC_STEP)
                        pwm.duty_u16(int(MAX_DUTY * dc / 100))
                elif cmd.upper() in ("X", "EXIT"):
                    break
                elif cmd.upper().startswith("F") and len(cmd) > 1:
                    try:
                        new_freq = int(cmd[1:])
                        if new_freq > 0:
                            freq = new_freq
                            pwm.freq(freq)
                    except ValueError:
                        print("Invalid frequency")
                elif cmd.upper().startswith("DC") and len(cmd) > 2:
                    try:
                        new_dc = int(cmd[2:])
                        if 0 <= new_dc <= 100:
                            dc = new_dc
                            pwm.duty_u16(int(MAX_DUTY * dc / 100))
                    except ValueError:
                        print("Invalid duty cycle")
                else:
                    print("Unknown command")
        except KeyboardInterrupt:
            print("\nStopping...")
        except EOFError:
            pass
        
        self.cleanup(pwm)


class Menu:
    def __init__(self):
        self.modes = {
            "1": ("Fixed Freq and DC", FixedMode()),
            "2": ("Fixed Freq, Moving DC", MovingDCMode()),
            "3": ("Interactive", InteractiveMode()),
        }
    
    def show(self):
        print("\nPWM Controller Menu")
        for key, (name, _) in self.modes.items():
            print(f"{key}. {name}")
        print("x. Exit")
        print("-" * 30)
    
    def run(self):
        while True:
            self.show()
            choice = input("Select option: ").strip()
            
            if choice == "x":
                print("Goodbye!")
                return
            
            if choice in self.modes:
                name, mode = self.modes[choice]
                result = mode.get_params()
                if result[0] is not None:
                    mode.run(*result)
            else:
                print("Invalid option")


def main():
    Menu().run()

if __name__ == "__main__":
    main()
