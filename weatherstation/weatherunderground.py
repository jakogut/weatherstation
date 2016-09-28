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

import urllib
import urllib.request
import urllib.parse

import pint # Unit conversion library

import logging

class WUAuthError(Exception):
    pass

class WUParameterError(Exception):
    pass

class WURequestFailedError(Exception):
    pass

class PWS(object):
    url = 'https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
    rapidfire_url = 'https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'

    def __init__(self, id, password, rapidfire=False):
        self._id = id
        self._password = password

        # Create the unit registry for conversions
        self.ureg = pint.UnitRegistry()

        self.logger = logging.getLogger('.' + self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        # Initialize our atmospheric conditions to None
        self._tempc = None
        self._kPa = None
        self._humd_pct = None
        self._uv = None

    def _request(self, url, parameters):
        params = urllib.parse.urlencode(parameters)
        response = urllib.request.urlopen('?'.join([url, params]))

        parsed_response = response.read().decode('UTF-8').strip()

        if parsed_response == 'success':
            return

        raise WURequestFailedError(parsed_response)

    def upload_outdoor(self, dt=None):
        # Upload weather conditions
        #
        # Arguments:
        # dt: UTC datetime of data capture, default is now 
        params = {
            'action': 'updateraw',
            'ID': self._id,
            'PASSWORD': self._password,
            'dateutc': dt if dt is not None else 'now',
            'tempf': self.tempf,
            'humidity': self.humidity_pct,
            'baromin': self.barom_inHg,
            'UV': self.uv
        }

        self.logger.info(
                'Uploading outdoor snapshot: {:.2f} F, {:.2f}% humidity, {:.2f} in Hg, {} UV index'.format(
                self.tempf, self.humidity_pct, self.barom_inHg, self.uv
            )
        )

        self._request(self.url, params)

    def upload_indoor(self, dt=None):
        # Upload indoor conditions
        # Arguments:
        # dt: UTC datetime of data capture, default is now 
        params = {
            'action': 'updateraw',
            'ID': self._id,
            'PASSWORD': self._password,
            'dateutc': dt if dt is not None else 'now',
            'indoortempf': self.tempf,
            'indoorhumidity': self.humidity_pct
        }

        self.logger.info(
                'Uploading indoor snapshot: {:.2f} F, {:.2f}% humidity, {:.2f} in Hg'.format(
                self.tempf, self.humidity_pct, self.barom_inHg
            )
        )

        self._request(self.url, params)

    # Internally, we store atmospheric conditions in metric, then convert if
    # the user requests them in imperial.

    @property
    def tempc(self):
        return self._tempc

    @tempc.setter
    def tempc(self, value):
        self._tempc = value

    @property
    def tempf(self):
        Q_ = self.ureg.Quantity
        quantity, unit = Q_(self._tempc, self.ureg.degC).to('degF').to_tuple()
        return quantity

    @tempf.setter
    def tempf(self, value):
        Q_ = self.ureg.Quantity
        quantity, unit = Q_(value, self.ureg.degF).to('degC').to_tuple()
        self._tempc = quantity

    @property
    def barom_kPa(self):
        return self._kPa

    @barom_kPa.setter
    def barom_kPa(self, value):
        self._kPa = value

    @property
    def barom_inHg(self):
        quantity, unit = (self._kPa * self.ureg.kPa).to(self.ureg.inHg).to_tuple()
        return quantity

    @barom_inHg.setter
    def barom_inHg(self, value):
        self._kPa = (value * self.ureg.inHg).to(self.ureg.kPa)

    @property
    def humidity_pct(self):
        return self._humd_pct

    @humidity_pct.setter
    def humidity_pct(self, value):
        self._humd_pct = value

    @property
    def uv(self):
        return self._uv

    @uv.setter
    def uv(self, value):
        self._uv = value

if __name__ == '__main__':
    from .bme280 import BME280
    from .si1145 import SI1145

    pws = PWS('KWAYAKIM48', 'rwvgd37g')

    env_sensor = BME280()
    uv_sensor = SI1145()
