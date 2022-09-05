from collections import defaultdict
from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent

DEBUG = True
UA = user_agent('safari')

LEVEL_TYPES = {
    'OFFLINE':      'data/offline.png',
    'VERY_LOW':     'data/very_low.png',
    'LOW':          'data/low.png',
    'MEDIUM':       'data/medium.png',
    'HIGH':         'data/high.png',
    'VERY_HIGH':    'data/very_high.png',
    'EXTREME':      'data/extreme.png',
    'AIRMAGEDDON':  'data/airmageddon.png'
}
UPDATED = f'⏳'
ADDRESS = f'🏠'
CURRENT_COORDINATES = f'⛳'
SET_COORDINATES = {
    'title': f'⚙️Set coordinates',
    'message': f'Set the coordinates where you want to monitor the air.\n '
               f'Copy the coordinates into Google Maps and paste them here.'
}
TIMER = f'⏱'
SET_TIMER = {
    'title': f'⚙️Set coordinates',
    'message': f'Set interval in seconds to wait before requesting the Airly API\n '
               f'Copy the coordinates into Google Maps and paste them here.'
}

class App():
    """
    System Tray app to connect to VPN
    """
    def __init__(self):
        # app initially set as None to signal when app starts
        self.app = None
        self.url = 'https://widget.airly.org/api/v1/'
        self.current_level = LEVEL_TYPES['OFFLINE']
        self.latitude = '52.2394646242'  # https://airly.org/map/en/#52.2394646242,21.0457174815
        self.longitude = '21.0457174815'
        self.interval = 60


    def run(self) -> None:
        """  Run App with parameters  """
        self.app = rumps.App("Quality Air Monitor", title=None, icon='data/offline.png')
        self.app.menu = [
            rumps.MenuItem(title=UPDATED, callback=self.refresh_status),
            rumps.MenuItem(title=ADDRESS),
            None,
            rumps.MenuItem(title=CURRENT_COORDINATES, callback=self.set_coordinates),
            None,
        ]
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

    def refresh_status(self,_):
        """Refresh AIRLY CAQI information on menu."""
        response = self.get_air_quality()

        if self.latitude and self.longitude:
            self.app.menu[CURRENT_COORDINATES].title = f'{CURRENT_COORDINATES}: {self.latitude}, {self.longitude}'
        else:
            self.app.menu[CURRENT_COORDINATES].title = f'{CURRENT_COORDINATES}: No coordinates'

        if response['level']:
            self.app.icon = response['level']
        else:
            self.app.icon = LEVEL_TYPES['OFFLINE']

        if response["updated"]:
            self.app.menu[UPDATED].title = f'{UPDATED}: {response["updated"]}'
        else:
            self.app.menu[UPDATED].title = f'{UPDATED}: Not updated'

        if response['address']:
            self.app.menu[ADDRESS].title = f'{ADDRESS}: {response["address"]}'
        else:
            self.app.menu[ADDRESS].title = f'{ADDRESS}: No address'

    def set_coordinates(self, _):
        """ Set address coordinates for monitoring  """
        setting_window = rumps.Window(
            title=SET_COORDINATES['title'],
            message=SET_COORDINATES['message'],
            default_text=f'{self.latitude}, {self.longitude}',
            ok='Save',
            cancel='Cancel',
        )

        response = setting_window.run()
        if response.clicked:
            latitude, longitude = str(response.text).strip().split(', ')
            self.latitude = latitude
            self.longitude = longitude

            self.refresh_status(None)

# class QAirMonApp(rumps.App):
#     @rumps.clicked(TIMER)
#     def set_timer(self, _):
#         """ Set interval in seconds to wait before requesting the Airly API  """
#         setting_window = rumps.Window(
#             title=SET_TIMER['title'],
#             message=SET_TIMER['message'],
#             default_text=f'{self.timer_interval}',
#             ok='Save',
#             cancel='Cancel',
#             dimensions=(100,20)
#         )
#
#         response = setting_window.run()
#         if response.clicked:
#             latitude, longitude = str(response.text).strip().split(', ')
#
#             if (payload := str(response.text).strip()).isnumeric():
#                 self.timer_interval = int(payload)


if __name__ == "__main__":
    # try:
    #     app = App()
    #     app.run()
    # except Exception as e:
    #     print("Error trying to start application: " + str(e))
    app = App()
    app.run()