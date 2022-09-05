from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent

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
UA = user_agent("safari")
UPDATED = "⏳"
ADDRESS = "🏠"
CURRENT_COORDINATES = '⛳'
SET_COORDINATES = {
    'title': f'⚙️Set coordinates',
    'message': f'Set the coordinates where you want to monitor the air.\n '
               f'Copy the coordinates into Google Maps and paste them here.'
}


class QAirMonApp(rumps.App):
    url = 'https://widget.airly.org/api/v1/'
    current_level = LEVEL_TYPES['OFFLINE']
    latitude = '52.2394646242'  # https://airly.org/map/en/#52.2394646242,21.0457174815
    longitude = '21.0457174815'

    @rumps.clicked(UPDATED)
    @rumps.timer(60)
    def refresh_status(self,_):
        """Refresh AIRLY CAQI information on menu."""
        self.menu[CURRENT_COORDINATES].title = f'{CURRENT_COORDINATES}: {self.latitude}, {self.longitude}'
        response = self.get_air_quality(None)
        if response:
            self.icon = response['level']
            self.menu[UPDATED].title = f'{UPDATED}: {response["updated"]}'
            self.menu[ADDRESS].title = f'{ADDRESS}: {response["address"]}'

    @rumps.clicked(CURRENT_COORDINATES)
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

    def get_air_quality(self, _) -> dict:
        """ Get air quality from Airly API """
        result = dict()

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

        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError:
            self.icon = LEVEL_TYPES['OFFLINE']
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)

        return result

if __name__ == "__main__":
    app = QAirMonApp("Quality Air Monitor", title=None, icon='data/offline.png')
    app.menu = [
        UPDATED,
        ADDRESS,
        None,
        CURRENT_COORDINATES,
        None,
    ]
    rumps.debug_mode(True)
    app.run()
