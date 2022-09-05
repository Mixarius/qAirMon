from collections import defaultdict
from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent

DEBUG = True
UA = user_agent('safari')

LEVEL_TYPES = {
    'OFFLINE': 'data/offline.png',
    'VERY_LOW': 'data/very_low.png',
    'LOW': 'data/low.png',
    'MEDIUM': 'data/medium.png',
    'HIGH': 'data/high.png',
    'VERY_HIGH': 'data/very_high.png',
    'EXTREME': 'data/extreme.png',
    'AIRMAGEDDON': 'data/airmageddon.png'
}
UPDATED = 'UPDATED'
ADDRESS = 'ADDRESS'
CURRENT_COORDINATES = f'CURRENT_COORDINATES'
TIMER = 'TIMER'



class App():
    """
    System Tray app to connect to VPN
    """
    def __init__(self):
        # app initially set as None to signal when app starts
        self.app = None
        self.timer = None
        self.timer_interval = 1
        self.timer_status = False
        self.url = 'https://widget.airly.org/api/v1/'
        self.current_level = LEVEL_TYPES['OFFLINE']
        self.latitude = '52.2394646242'  # https://airly.org/map/en/#52.2394646242,21.0457174815
        self.longitude = '21.0457174815'

    def run(self):
        """  Run App with parameters  """
        self.app = rumps.App("Quality Air Monitor", title=None, icon='data/offline.png')
        self.app.menu = [
            rumps.MenuItem(title=UPDATED, callback=self.refresh_status, icon='data/updated.png'),
            rumps.MenuItem(title=ADDRESS, icon='data/address.png'),
            None,
            rumps.MenuItem(title=CURRENT_COORDINATES, callback=self.set_coordinates, icon='data/set_coordinates.png'),
            rumps.MenuItem(title=TIMER, callback=self.set_timer, icon='data/timer.png'),
            None,
        ]

        self.timer = rumps.Timer(callback=self.refresh_status, interval=self.timer_interval*60)
        rumps.debug_mode(DEBUG)

        self.refresh_status(None)
        self.app.run()

    def get_air_quality(self) -> defaultdict:
        """ Get air quality from Airly API """
        result = defaultdict(str)

        if not self.latitude or not self.longitude:
            return result

        headers = {
            'Origin': 'https://airly.org',
            'Accept-Encoding': 'gzip, deflate, br',
            'Host': 'widget.airly.org',
            'User-Agent': UA,
            'Accept-Language': 'en-gb',
            'Referer': 'https://airly.org/',
        }

        params = {
            'displayMeasurements': 'false',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'id': 'null',
            'indexType': 'AIRLY_CAQI',
            'language': 'en',
            'unitSpeed': 'metric',
            'unitTemperature': 'celsius'
        }

        try:
            response = requests.get(url=self.url, headers=headers, params=params)
            if response and response.status_code == 200:
                json_data = response.json()

                result['level'] = LEVEL_TYPES[json_data['level']]
                result['address'] = json_data["address"]

                datetime_object = datetime.strptime(json_data['date'], '%Y-%m-%dT%H:%M:%S.%fZ')
                datetime_str = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
                result['updated'] = datetime_str

        except requests.exceptions.ConnectionError as err:
            print("Connection Error:", err)
        except requests.exceptions.HTTPError as err:
            print("Http Error:", err)
        except requests.exceptions.Timeout as err:
            print("Timeout Error:", err)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)

        return result

    def refresh_status(self, _):
        """Refresh AIRLY CAQI information on menu."""
        response = self.get_air_quality()

        if self.timer_interval:
            self.app.menu[TIMER].title = f'Timer ON. Every {self.timer_interval} min.'
            self.timer.interval = self.timer_interval * 60
            self.app.menu[TIMER].state = 1
        else:
            self.app.menu[TIMER].title = f'Timer OFF. No interval specified'
            self.app.menu[TIMER].state = 0

        if self.latitude and self.longitude:
            self.app.menu[CURRENT_COORDINATES].title = f'{self.latitude}, {self.longitude}'
        else:
            self.app.menu[CURRENT_COORDINATES].title = f'No coordinates'

        if response['level'] and self.app.menu[TIMER].state:
            self.app.icon = response['level']
        else:
            self.app.icon = LEVEL_TYPES['OFFLINE']

        if response["updated"]:
            self.app.menu[UPDATED].title = f'Updated: {response["updated"]}'
        else:
            self.app.menu[UPDATED].title = f'Not updated'

        if response['address']:
            self.app.menu[ADDRESS].title = f'{response["address"]}'
        else:
            self.app.menu[ADDRESS].title = f'No address'

    def set_coordinates(self, _):
        """ Set address coordinates for monitoring  """
        setting_window = rumps.Window(
        title='Coordinates',
            message=f'Set the coordinates where you want to monitor the air.\n '
                    f'Copy the coordinates into Google Maps and paste them here.',
            default_text=f'{self.latitude}, {self.longitude}',
            ok='Save',
            cancel='Cancel'
        )
        setting_window.icon = 'data/setting.png'

        response = setting_window.run()
        if response.clicked:
            latitude, longitude = str(response.text).strip().split(', ')
            self.latitude = latitude
            self.longitude = longitude

            self.refresh_status(None)

    def set_timer(self, _):
        """ Set interval in seconds to wait before requesting the Airly API  """
        setting_window = rumps.Window(
            title='Timer',
            message=f'Set interval in minutes to wait before requesting '
                    f'the Airly API and the timer will be ON.\nIf value is 0 then timer is OFF',
            default_text=f'{self.timer_interval}',
            ok='Save',
            cancel='Cancel',
            dimensions=(100, 20)
        )
        setting_window.icon = 'data/setting.png'
        response = setting_window.run()
        if response.clicked:
            if (payload := str(response.text).strip()).isnumeric():
                self.timer_interval = int(payload)
                self.refresh_status(None)



if __name__ == "__main__":
    app = App()
    app.run()
    # try:
    #     app = App()
    #     app.run()
    # except Exception as e:
    #     print("Error trying to start application: " + str(e))
