from collections import defaultdict
from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent

DEBUG = True
UA = user_agent('safari')

APP_ICON = {
    '': 'data/levels/offline.png',
    'VERY_LOW': 'data/levels/very_low.png',
    'LOW': 'data/levels/low.png',
    'MEDIUM': 'data/levels/medium.png',
    'HIGH': 'data/levels/high.png',
    'VERY_HIGH': 'data/levels/very_high.png',
    'EXTREME': 'data/levels/extreme.png',
    'AIRMAGEDDON': 'data/levels/airmageddon.png'
}

LEVEL_ICON = {
    '': '🔵️',
    'VERY_LOW': '✅',
    'LOW': '🟢️',
    'MEDIUM': '🟡',
    'HIGH': '🟠',
    'VERY_HIGH': '🔴',
    'EXTREME': '🔴',
    'AIRMAGEDDON': '🟣'
}


class App:
    """
    System Tray app for monitoring air quality via Airly API
    """
    def __init__(self):
        self.app = None
        self.timer = None
        self.url = 'https://widget.airly.org/api/v1/'
        self.current_level = ''
        self.latitude = '52.2394646242'  # https://airly.org/map/en/#52.2394646242,21.0457174815
        self.longitude = '21.0457174815'

    def run(self):
        """  Run App with parameters  """
        self.app = rumps.App("Quality Air Monitor", title=None, icon=APP_ICON[''])
        self.app.menu = [
            rumps.MenuItem(title='Check Now', callback=self.refresh_status),
            rumps.MenuItem(title='Pause Checking', callback=self.switch_timer),
            None,
            rumps.MenuItem(title='DATE'),
            rumps.MenuItem(title='DESCRIPTION', callback=self.send_notification),
            rumps.MenuItem(title='ADDRESS'),
            rumps.MenuItem(title='CURRENT_COORDINATES'),
            None,
            [rumps.MenuItem(title='Preferences'),
             [rumps.MenuItem(title='Set coordinates', callback=self.set_coordinates),
              rumps.MenuItem(title='Set timer interval', callback=self.set_timer_interval)]],
            None,
        ]

        self.timer = rumps.Timer(callback=self.refresh_status, interval=300)
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

                result['level'] = json_data['level']
                result['address'] = json_data['address']

                datetime_object = (
                        datetime.strptime(json_data['date'], '%Y-%m-%dT%H:%M:%S.%fZ') +
                        (datetime.now() - datetime.utcnow())
                )
                result['date'] = datetime_object.strftime('%Y-%m-%d %H:%M:%S')

                result['description'] = json_data['description']

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
        """ Update timer status in the menu """
        self.app.menu['Pause Checking'].state = not self.timer.is_alive()

    def refresh_status(self, _):
        """Refresh AIRLY CAQI information on menu."""
        response = self.get_air_quality()

        description = (f'{response["description"]}' if response['description']
                       else f'🏠 Not description')
        self.app.menu['DESCRIPTION'].title = (f'{LEVEL_ICON[response["level"]]} '
                                              f'{description}')

        self.app.menu['DATE'].title = (f'📅 {response["date"]}'
                                       if response["date"] else f'📅 Not checked')

        self.app.menu['ADDRESS'].title = (f'🏠 {response["address"]}'
                                          if response['address'] else f'🏠Not address')

        self.app.menu['CURRENT_COORDINATES'].title = (f'⛳ {self.latitude},'
                                                      f' {self.longitude}')

        self.refresh_status_timer(None)

        self.app.icon = APP_ICON[response["level"]]

        if self.current_level != response['level']:
            self.current_level = response['level']
            self.send_notification(None)

    def set_coordinates(self, _):
        """ Set address coordinates for monitoring  """
        setting_window = rumps.Window(
            title='Coordinates',
            message=f'Set the coordinates where you want to monitor the air.\n '
                    f'Copy the coordinates into Google Maps and paste them here.\n'
                    f'For example: 52.23955, 21.045800',
            default_text=f'{self.latitude}, {self.longitude}',
            ok='Save',
            cancel='Cancel'
        )
        setting_window.icon = 'data/setting.png'

        response = setting_window.run()
        if response.clicked:
            self.latitude, self.longitude = (s.strip() for s in str(response.text).split(','))
            self.refresh_status(None)

    def set_timer_interval(self, _):
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

        setting_window.icon = 'data/setting.png'
        response = setting_window.run()
        if response.clicked:
            if (payload := str(response.text).strip()).isnumeric():
                self.timer.interval = int(payload)*60
                self.refresh_status_timer(None)

    def switch_timer(self, _):
        """ Switching timer function """
        if self.timer.is_alive():
            self.timer.stop()
            self.refresh_status_timer(None)
            self.app.icon = APP_ICON['']
        else:
            self.timer.start()
            self.refresh_status(None)

    def send_notification(self, _):
        title = self.app.menu['DESCRIPTION'].title
        subtitle = None
        message = self.app.menu['ADDRESS'].title

        rumps.notification(title, subtitle, message, data=None, sound=True)


if __name__ == "__main__":
    app = App()
    app.run()
    # try:
    #     app = App()
    #     app.run()
    # except Exception as e:
    #     print("Error trying to start application: " + str(e))
