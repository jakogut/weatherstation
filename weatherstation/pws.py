from weatherstation.bme280 import BME280
from weatherstation.si1145 import SI1145
from weatherstation.weatherunderground import PWS

import weatherstation.web as web

import sys
import time
import logging
from configparser import ConfigParser

from threading import Thread

class Daemon(Thread):
    running = True

    def __init__(self, id, password, display_units='imperial', busnum=2, idle_interval=300):
        super().__init__()

        self.id = id
        self.password = password
        self.display_units = display_units

        self._idle_interval = idle_interval

        self.atm_sensor = BME280(busnum=busnum)
        self.uv_sensor = SI1145(busnum=busnum)

        # The atmospheric sensor wants to be read from first, to introduce
        # a bit of delay
        self.atm_sensor.read_raw_temp()

        self.pws = PWS(id, password)

    def _idle(self):
        time.sleep(self._idle_interval)

    def _update(self):
        print('Updating PWS')
        self.pws.tempc = self.atm_sensor.read_temperature()
        self.pws.barom_kPa = self.atm_sensor.read_pressure() / 1000.0
        self.pws.humidity_pct = self.atm_sensor.read_humidity()
        self.pws.uv = self.uv_sensor.readUV() / 100.00

        self.pws.upload_outdoor()

        if self.display_units == 'imperial':
            web.env_data['temp'] = '{:.2f} deg F'.format(self.pws.tempf)
            web.env_data['press'] = '{:.2f} in Hg'.format(self.pws.barom_inHg)
            web.env_data['humd'] = '{:.2f}%'.format(self.pws.humidity_pct)
            web.env_data['uv'] = '{:.2f}'.format(self.pws.uv)
        elif self.display_units == 'metric':
            web.env_data['temp'] = '{:.2f} deg C'.format(self.pws.tempc)
            web.env_data['press'] = '{:.2f} mPa'.format(self.pws.barom_mPa)
            web.env_data['humd'] = '{:.2f}%'.format(self.pws.humidity_pct)
            web.env_data['uv'] = '{:.2f}'.format(self.pws.uv)

    def run(self):
        while self.running:
            self._update()
            self._idle()

    def stop(self):
        self.running = False
        self.join()

def init_logger():
    logger = logging.getLogger()

    formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    return logger

def init_config():
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print('Usage: {} CONFIG_FILE'.format(sys.argv[0]))
        sys.exit()
    
    config = ConfigParser(interpolation=None)
    config.read(config_path)

    return config

if __name__ == '__main__':
    root_logger = init_logger()
    root_logger.info('Starting weather station')

    config = init_config()

    pws_daemon = Daemon(
        config.get('pws', 'id'),
        config.get('pws', 'password'),
        config.get('web', 'display_units')
    )

    try:
        pws_daemon.start()
        web.app.run(host=config.get('web', 'listen_address'),
                    port=config.get('web', 'port'))

    except KeyboardInterrupt:
        root_logger.info('Shutting down...')
        pws_daemon.stop()
        raise
