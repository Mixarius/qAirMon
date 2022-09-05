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


class QAirMonApp(rumps.App):
    url = 'https://widget.airly.org/api/v1/'

    @rumps.timer(60)
    def get_air_quality(self) -> None:
        """ Get air quality from Airly API """
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
            'latitude': '52.2394646242', # https://airly.org/map/en/#52.2394646242,21.0457174815
            'longitude': '21.0457174815',
            'id': 'null',
            'indexType': 'AIRLY_CAQI',
            'language': 'en',
            'unitSpeed': 'metric',
            'unitTemperature': 'celsius'
        }

        try:
            response = requests.get(url=self.url, headers=headers, params=params)
            if response and response.status_code == 200:
                level = response.json()['level']
                self.icon = LEVEL_TYPES[level]
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError:
            self.icon = LEVEL_TYPES['OFFLINE']
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)


if __name__ == "__main__":
    app = QAirMonApp("Quality Air Monitor", title=None, icon='data/offline.png')
    rumps.debug_mode(True)
    app.run()
