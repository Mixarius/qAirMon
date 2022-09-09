from collections import defaultdict
from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent

DEBUG = True
UA = user_agent('safari')

LEVEL_TYPES = {
    'OFFLINE': 'data/levels/offline.png',
    'VERY_LOW': 'data/levels/very_low.png',
    'LOW': 'data/levels/low.png',
    'MEDIUM': 'data/levels/medium.png',
    'HIGH': 'data/levels/high.png',
    'VERY_HIGH': 'data/levels/very_high.png',
    'EXTREME': 'data/levels/extreme.png',
    'AIRMAGEDDON': 'data/levels/airmageddon.png'
}


class App:
    """
    System Tray app for monitoring air quality via Airly API
    """
    def __init__(self):
        self.app = None
        self.timer = None
        self.url = 'https://widget.airly.org/api/v1/'
        self.current_level = LEVEL_TYPES['OFFLINE']
        self.latitude = '52.2394646242'  # https://airly.org/map/en/#52.2394646242,21.0457174815
        self.longitude = '21.0457174815'

    def run(self):
        """  Run App with parameters  """
        self.app = rumps.App("Quality Air Monitor", title=None, icon='data/levels/offline.png')
        self.app.menu = [
            rumps.MenuItem(title='UPDATED', callback=self.refresh_status, icon='data/updated.png'),
            rumps.MenuItem(title='ADDRESS', icon='data/address.png'),
            rumps.MenuItem(title='CURRENT_TIMER'),
            None,
            rumps.MenuItem(title='CURRENT_COORDINATES', callback=self.set_coordinates, icon='data/set_coordinates.png'),
            rumps.MenuItem(title=f'⚙️️Timer settings', callback=self.set_timer),
            None,
        ]

        self.timer = rumps.Timer(callback=self.refresh_status, interval=60)
        self.timer.start()
        rumps.debug_mode(DEBUG)
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

    def refresh_status_timer(self, _):
        timer_status = 'ON' if self.timer.is_alive() else 'OFF'
        self.app.menu[
            'CURRENT_TIMER'].title = f'⏱Timer {timer_status}. Repeat the request every {self.timer.interval // 60} min.'
        self.app.menu['CURRENT_TIMER'].state = self.timer.is_alive()

    def refresh_status(self, _):
        """Refresh AIRLY CAQI information on menu."""
        response = self.get_air_quality()

        self.refresh_status_timer(None)

        if self.latitude and self.longitude:
            self.app.menu['CURRENT_COORDINATES'].title = f'{self.latitude}, {self.longitude}'
        else:
            self.app.menu['CURRENT_COORDINATES'].title = f'No coordinates'

        if response['level'] and self.timer.is_alive():
            self.app.icon = response['level']
        else:
            self.app.icon = LEVEL_TYPES['OFFLINE']

        if response["updated"]:
            self.app.menu['UPDATED'].title = f'Updated: {response["updated"]}'
        else:
            self.app.menu['UPDATED'].title = f'Not updated'

        if response['address']:
            self.app.menu['ADDRESS'].title = f'{response["address"]}'
        else:
            self.app.menu['ADDRESS'].title = f'No address'

    def set_coordinates(self, _):
        """ Set address coordinates for monitoring  """
        setting_window = rumps.Window(
            title='Coordinates',
            message=f'Set the coordinates where you want to monitor the air.\n '
                    f'Copy the coordinates into Google Maps and paste them here.\n'
                    f'For example: 52.23984247229307, 21.045780515509897',
            default_text=f'{self.latitude}, {self.longitude}',
            ok='Save',
            cancel='Cancel'
        )
        setting_window.icon = 'data/setting.png'

        response = setting_window.run()
        if response.clicked:
            latitude, longitude = (s.strip() for s in str(response.text).split(','))
            if latitude.isnumeric() and longitude.isnumeric():
                self.latitude = latitude.strip()
                self.longitude = longitude.strip()

            self.refresh_status(None)

    def set_timer(self, _):
        """ Set interval in seconds to wait before requesting the Airly API  """
        setting_window = rumps.Window(
            title='Timer',
            message=f'Set interval in minutes to wait before requesting the Airly.'
                    f'',
            default_text=f'{self.timer.interval//60}',
            ok='Save',
            cancel='Cancel',
            dimensions=(100, 20)
        )
        timer_status = 'Turn OFF' if self.timer.is_alive() else 'Turn ON'
        setting_window.add_button(timer_status)
        setting_window.icon = 'data/setting.png'
        response = setting_window.run()
        if response.clicked == 1:
            if (payload := str(response.text).strip()).isnumeric():
                self.timer.interval = int(payload)*60
                self.refresh_status_timer(None)

        elif response.clicked == 2:
            if self.timer.is_alive():
                self.timer.stop()
            else:
                self.timer.start()
            self.refresh_status_timer(None)

if __name__ == "__main__":
    app = App()
    app.run()
    # try:
    #     app = App()
    #     app.run()
    # except Exception as e:
    #     print("Error trying to start application: " + str(e))
