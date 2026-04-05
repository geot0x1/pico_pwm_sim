from machine import Pin, PWM
import time

PIN = 17
MAX_DUTY = 65535

class PWMMode:
    def get_params(self):
        raise NotImplementedError
    
    def run(self, freq, dc):
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
                return None, None
            return freq, dc
        except ValueError:
            print("Invalid input. Please enter numbers.")
            return None, None

    def run(self, freq, dc):
        pwm = PWM(Pin(PIN))
        pwm.freq(freq)
        duty_u16 = int(MAX_DUTY * dc / 100)
        pwm.duty_u16(duty_u16)
        
        print(f"\nRunning PWM: {freq}Hz at {dc}% duty cycle")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.cleanup(pwm)
        print("\nPWM stopped")


class Menu:
    def __init__(self):
        self.modes = {
            "1": ("Fixed Freq and DC", FixedMode()),
        }
    
    def show(self):
        print("\nPWM Controller Menu")
        for key, (name, _) in self.modes.items():
            print(f"{key}. {name}")
        print("x. Exit")
        print("-" * 30)
    
    def run(self):
        self.show()
        choice = input("Select option: ").strip()
        
        if choice == "x":
            print("Goodbye!")
            return
        
        if choice in self.modes:
            name, mode = self.modes[choice]
            freq, dc = mode.get_params()
            if freq is not None:
                mode.run(freq, dc)
        else:
            print("Invalid option")


def main():
    Menu().run()

if __name__ == "__main__":
    main()
