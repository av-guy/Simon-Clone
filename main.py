import RPi.GPIO as GPIO
import time
import random

GPIO.setmode(GPIO.BCM)


class LED:
    """
        Implements an abstract LED class

        Main methods:
        toggle - Toggles the LED on or off
        status - Returns the current status of the LED
    """
    def __init__(self, gpio_port, color):
        self.gpio_port = gpio_port
        self.type = 'DIGITAL'
        self.color = color
        GPIO.setup(gpio_port, GPIO.OUT)

    def toggle(self, directive):
        """
            Toggle the LED on and off based on the directive
            @params
                directive - On or Off depending on desired state

            @returns
                None
        """
        if directive == 'On':
            GPIO.output(self.gpio_port, GPIO.HIGH)
        else:
            GPIO.output(self.gpio_port, GPIO.LOW)
        return None

    def status(self):
        """
            Return the status of the LED

            @returns
                str - 'On' or 'Off'
        """
        _status = GPIO.input(self.gpio_port)
        if _status:
            return 'On'
        return 'Off'


class Button:
    """
        Implements an abstract Button class

        Main methods:
        released - Returns whether or not button is released
        cooling - Provides a cooloff timer for the button to prevent
                  unintended press repeats
    """
    def __init__(self, button_port):
        self.button_port = button_port
        GPIO.setup(button_port, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.last_time = None

    def released(self):
        """ Returns whether or not button is released """
        return GPIO.input(self.button_port)

    def cooling(self):
        """
            Returns the number of seconds since the last button press

            @returns
                int - number of seconds passed since last press
        """
        seconds = None
        if self.last_time:
            seconds = time.time() - self.last_time
        self.last_time = time.time()
        if not seconds:
            return 10
        return seconds


class Pair:
    """ Class to pair a button with an LED """
    def __init__(self, button, led):
        self.button = button
        self.led = led


class Game:
    """
        Game class to regulate game behavior

        Main methods:
        start - Starts the game by performing a few steps
        show_pattern - Shows the current in-memory pattern
        watch_pair - Watches a pair of items to regulate game behavior
        run - The game loop that regulates the game
        reset - Starts the game over again
    """
    def __init__(self, pairs):
        self.pairs = pairs
        self.speed = 1.00
        self.pattern = Pattern(pairs)
        self.index = 0

    def start(self):
        """
            Starts the game by cycling the lights (both forwards and reverse),
            generates a new light pattern for the player, and then shows that
            pattern
        """
        self.pattern.cycle_lights()
        self.pattern.generate()
        self.show_pattern()
        return None

    def show_pattern(self):
        """
            Displays the pattern for the player based on the calculated speed
        """
        for pair in self.pattern.pattern:
            pair.led.toggle('On')
            time.sleep(self.speed)
            pair.led.toggle('Off')
            time.sleep(0.2)

    def watch_pair(self, pair):
        """
            Watches a pair of items, prevents repeat presses that happen in
            quick succession to provide more reliable game behavior

            @params
                pair - a button and LED pair

            @returns
                None
        """
        if not pair.button.released():
            cooling = pair.button.cooling()
            if pair.led.status() == 'Off':
                if cooling > 0.05:
                    if pair.button is self.pattern.pattern[self.index].button:
                        self.index += 1
                    else:
                        self.reset()
                pair.led.toggle('On')
        else:
            pair.led.toggle('Off')
        return None

    def run(self):
        """
            Runs the game while in a loop. Watches pairs for button activity.
            If the index value matches the pattern length, that means the
            player has correctly guessed the pattern pairs. It then adds a
            light to the pattern and shows the pattern
        """
        if self.index >= len(self.pattern.pattern):
            for pair in self.pairs:
                pair.led.toggle('Off')
            self.speed -= 0.1
            self.pattern.add()
            self.show_pattern()
            self.index = 0
        self.watch_pair(self.pairs[0])
        self.watch_pair(self.pairs[1])
        self.watch_pair(self.pairs[2])
        self.watch_pair(self.pairs[3])

    def reset(self):
        """ Resets the game """
        self.index = 0
        self.speed = 1.00
        self.pattern.generate()
        self.pattern.cycle_lights()
        self.show_pattern()


class Pattern:
    def __init__(self, pairs):
        self.pairs = pairs
        self.new = False
        self.cycle = 0.06
        self.generate()

    def add(self):
        self.pattern.append(random.choice(self.pairs))
        self.new = True
        return True

    def generate(self):
        self.pattern = []
        for item in range(0, 3):
            self.pattern.append(random.choice(self.pairs))
        self.new = True
        return True

    def cycle_forward(self):
        for i in range(1, len(self.pairs)):
            self.pairs[i].led.toggle('On')
            time.sleep(self.cycle)
            self.pairs[i].led.toggle('Off')

    def cycle_backward(self):
        for i in range(len(self.pairs) - 2, -1, -1):
            self.pairs[i].led.toggle('On')
            time.sleep(self.cycle)
            self.pairs[i].led.toggle('Off')

    def cycle_lights(self):
        iterations = 0
        while iterations < 10:
            self.cycle_forward()
            self.cycle_backward()
            iterations += 1


if __name__ == "__main__":
    GPIO.cleanup()
    yellow_led = LED(18, 'yellow')
    blue_led = LED(23, 'blue')
    green_led = LED(19, 'green')
    red_led = LED(20, 'red')
    yellow_button = Button(17)
    blue_button = Button(16)
    green_button = Button(13)
    red_button = Button(12)
    yellow_pair = Pair(yellow_button, yellow_led)
    blue_pair = Pair(blue_button, blue_led)
    green_pair = Pair(green_button, green_led)
    red_pair = Pair(red_button, red_led)
    pairs = [yellow_pair, blue_pair, green_pair, red_pair]
    game = Game(pairs)
    game.start()
    try:
        while 1:
            game.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
