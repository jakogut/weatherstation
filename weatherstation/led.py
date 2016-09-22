from threading import Thread
import time

from periphery import GPIO

class LEDController(Thread):
    idle_interval = 0.01
    commands = ['on', 'off', 'blink', 'blink_once']
    blink_interval = 0.5

    running = True
    daemon = True

    def __init__(self, config, **kwargs):
        super(LEDController, self).__init__(**kwargs)

        self.led_context = {
            led_name: {'cmd': 'off', 'state': False, 'last_mod': 0}
            for led_name in dict(config.items('led')).keys() 
        }

        for name, led in self.led_context.items():
            led['gpio'] = GPIO(config.getint('led', name), 'out')

    def __del__(self):
        for led in self.led_context.values():
            led['gpio'].write(False)
            led['gpio'].close()

    def set(self, name, cmd):
        if cmd not in self.commands:
            raise ValueError(
                    'Invalid command, supported commands are: {}'.format(self.commands))

        self.led_context[name]['cmd'] = cmd

    def run(self):
        while(self.running):
            self._update()
            self._idle()

    def stop(self):
        self.running = False
        self.join()

    def _update(self):
        for led in self.led_context.values():
            if led['cmd'] == 'on':
                led['state'] = True
            elif led['cmd'] == 'off':
                led['state'] = False
            elif led['cmd'] == 'blink_once':
                    led['state'] = not led['state']
                    led['last_mod'] = time.time()

                    if time.time() - led['last_mod'] > self.blink_interval:
                        led['cmd'] = 'off'

            elif led['cmd'] == 'blink' and time.time() - led['last_mod'] > self.blink_interval:
                led['state'] = not led['state']
                led['last_mod'] = time.time()

            led['gpio'].write(led['state'])

    def _idle(self):
        time.sleep(self.idle_interval)

if __name__ == '__main__':
    from configparser import ConfigParser
    
    config = ConfigParser()
    config.add_section('led')
    config.set('led', 'network',    '44')
    config.set('led', 'hb',         '23')
    config.set('led', 'pwr',        '86')
    config.set('led', 'relay_a',    '66')
    config.set('led', 'relay_b',    '67')

    leds = LEDController(config)
    leds.start()

    for led in ['network', 'hb', 'relay_a', 'relay_b']:
        leds.set(led, 'blink')
        time.sleep(0.05)

    time.sleep(10)
    leds.stop()
