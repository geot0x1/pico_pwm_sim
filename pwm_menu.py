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
            delay = float(input("Enter delay per step (seconds): "))
            if dc_step <= 0 or delay <= 0:
                print("Step and delay must be positive")
                return None, None, None, None
            return freq, None, dc_step, delay
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return None, None, None, None

    def run(self, freq=None, dc=None, step=None, delay=None):
        pwm = PWM(Pin(PIN))
        pwm.freq(freq)
        
        duty = 0
        direction = 1
        step_u16 = int(MAX_DUTY * step / 100)
        
        print(f"\nRunning PWM: {freq}Hz, DC step: {step}%, delay: {delay}s")
        print("Press Ctrl+C to go back to menu")
        
        try:
            while True:
                pwm.duty_u16(duty)
                current_dc = int(duty / MAX_DUTY * 100)
                print(f"Duty cycle: {current_dc}%")
                time.sleep(delay)
                duty += step_u16 * direction
                if duty >= MAX_DUTY:
                    direction = -1
                elif duty <= 0:
                    direction = 1
        except KeyboardInterrupt:
            print("\nStopping...")
        
        self.cleanup(pwm)


class Menu:
    def __init__(self):
        self.modes = {
            "1": ("Fixed Freq and DC", FixedMode()),
            "2": ("Fixed Freq, Moving DC", MovingDCMode()),
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
