# Copyright (c) 2016 Joseph Kogut

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from threading import Thread
import time

from periphery import GPIO

class RelayController(Thread):
    idle_interval = 0.01
    commands = ['on', 'off']

    running = True
    daemon = True

    def __init__(self, config, **kwargs):
        super(RelayController, self).__init__(**kwargs)

        self.relay_context = {
                relay_name: {'cmd': 'off'}
            for relay_name in dict(config.items('relay')).keys() 
        }

        for name, relay in self.relay_context.items():
            relay['gpio'] = GPIO(config.getint('relay', name), 'out')

    def __del__(self):
        for relay in self.relay_context.values():
            relay['gpio'].write(False)
            relay['gpio'].close()

    def set(self, name, cmd):
        if cmd not in self.commands:
            raise ValueError(
                    'Invalid command, supported commands are: {}'.format(self.commands))

        self.relay_context[name.lower()]['cmd'] = cmd

    def run(self):
        while(self.running):
            self._update()
            self._idle()

    def stop(self):
        self.running = False
        self.join()

    def _update(self):
        for relay in self.relay_context.values():
            if relay['cmd'] == 'on':
                relay['state'] = True
            elif relay['cmd'] == 'off':
                relay['state'] = False

            relay['gpio'].write(relay['state'])

    def _idle(self):
        time.sleep(self.idle_interval)

if __name__ == '__main__':
    from configparser import ConfigParser
    
    config = ConfigParser()
    config.add_section('relay')
    config.set('relay', 'a', '66')
    config.set('relay', 'b', '67')

    relays = RelayController(config)
    relays.start()

    for relay in ['a', 'b']:
        relays.set(relay, 'on')
        time.sleep(1)

    time.sleep(10)
    relays.stop()
