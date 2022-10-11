import os
from collections import defaultdict
from datetime import datetime

import requests
import rumps
from fake_user_agent import user_agent
from easysettings import EasySettings

VERSION = "v0.1.1"
DEBUG = True
UA = user_agent("safari")
WIDGET_URL = "https://widget.airly.org/api/v1/"
MAP_URL = "https://airly.org/map/en/#"
GITHUB_URL = "https://github.com/Mixarius/qAirMon"
APP_ICON = {
    "": "data/levels/offline.png",
    "VERY_LOW": "data/levels/very_low.png",
    "LOW": "data/levels/low.png",
    "MEDIUM": "data/levels/medium.png",
    "HIGH": "data/levels/high.png",
    "VERY_HIGH": "data/levels/very_high.png",
    "EXTREME": "data/levels/extreme.png",
    "AIRMAGEDDON": "data/levels/airmageddon.png",
}
LEVEL_ICON = {
    "": "🔵️",
    "VERY_LOW": "✅",
    "LOW": "🟢️",
    "MEDIUM": "🟡",
    "HIGH": "🟠",
    "VERY_HIGH": "🔴",
    "EXTREME": "🔴",
    "AIRMAGEDDON": "🟣",
}
LEVEL_MESSAGE = {
    "": "",
    "VERY_LOW": "Very low",
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High",
    "VERY_HIGH": "Very high",
    "EXTREME": "Extreme",
    "AIRMAGEDDON": "Airmagedon",
}

settings = EasySettings("QAirMon.conf")


def get_air_quality() -> defaultdict:
    """Get air quality from Airly API"""
    result = defaultdict(str)

    headers = {
        "Origin": "https://airly.org",
        "Accept-Encoding": "gzip, deflate, br",
        "Host": "widget.airly.org",
        "User-Agent": UA,
        "Accept-Language": "en-gb",
        "Referer": "https://airly.org/",
    }

    params = {
        "displayMeasurements": "false",
        "latitude": settings.get("latitude"),
        "longitude": settings.get("longitude"),
        "id": "null",
        "indexType": "AIRLY_CAQI",
        "language": "en",
        "unitSpeed": "metric",
        "unitTemperature": "celsius",
    }

    try:
        response = requests.get(url=WIDGET_URL, headers=headers, params=params)
        if response and response.status_code == 200:
            json_data = response.json()

            result["level"] = json_data["level"]
            result["address"] = json_data["address"]

            datetime_object = datetime.strptime(
                json_data["date"], "%Y-%m-%dT%H:%M:%S.%fZ"
            ) + (datetime.now() - datetime.utcnow())
            result["date"] = datetime_object.strftime("%Y-%m-%d %H:%M:%S")

            result["description"] = json_data["description"]

    except requests.exceptions.ConnectionError as err:
        print("Connection Error:", err)
    except requests.exceptions.HTTPError as err:
        print("Http Error:", err)
    except requests.exceptions.Timeout as err:
        print("Timeout Error:", err)
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)

    return result


def go_to_airly_map(_):
    os.system(
        f"open \"\" {MAP_URL}{settings.get('latitude')},{settings.get('longitude')}"
    )


def go_to_github(_):
    os.system(f'open "" {GITHUB_URL}')


class App:
    """
    System Tray app for monitoring air quality via Airly API
    """

    def __init__(self):
        self.app = None
        self.timer = None
        self.current_level = ""

    def run(self):
        """Run App with parameters"""
        rumps.debug_mode(DEBUG)

        self.app = rumps.App("Quality Air Monitor", title=None)
        self.app.menu = [
            rumps.MenuItem(title="Check Now", callback=self.refresh_status),
            rumps.MenuItem(title="Pause Checking", callback=self.switch_timer),
            None,
            rumps.MenuItem(title="DATE"),
            rumps.MenuItem(title="DESCRIPTION", callback=self.send_notification),
            [
                rumps.MenuItem(title="ADDRESS"),
                [rumps.MenuItem(title="Show on map Airly", callback=go_to_airly_map)],
            ],
            None,
            [
                rumps.MenuItem(title="Preferences"),
                [
                    rumps.MenuItem(
                        title="Set coordinates", callback=self.set_coordinates
                    ),
                    rumps.MenuItem(
                        title="Set timer interval", callback=self.set_timer_interval
                    ),
                ],
            ],
            None,
            [
                rumps.MenuItem(title="About"),
                [
                    rumps.MenuItem(title=f"Quality Air Monitor {VERSION}"),
                    rumps.MenuItem(title="Open on Github", callback=go_to_github),
                ],
            ],
            None,
        ]

        self.timer = rumps.Timer(
            callback=self.refresh_status, interval=settings.get("timer_interval")
        )

        self.set_timer_activity(settings.get_bool("timer_enabled"))

        self.app.menu["DATE"].title = f"📅 Not checked"
        self.app.menu["DESCRIPTION"].title = f'{LEVEL_ICON[""]} ' f"Not description"
        self.app.menu["ADDRESS"].title = f"🏠 Not address"
        self.app.menu["Pause Checking"].state = not settings.get_bool("timer_enabled")
        self.app.icon = APP_ICON[""]
        self.app.run()

    def refresh_status(self, forced):
        """Refresh AIRLY CAQI information on menu."""
        response = defaultdict(str)

        if settings.get_bool("timer_enabled") or forced is not None:
            response = get_air_quality()

        description = (
            f'{response["description"]}'
            if response["description"]
            else f"Not description"
        )
        self.app.menu["DESCRIPTION"].title = (
            f'{LEVEL_ICON[response["level"]]} ' f"{description}"
        )

        self.app.menu["DATE"].title = (
            f'📅 {response["date"]}' if response["date"] else f"📅 Not checked"
        )

        self.app.menu["ADDRESS"].title = (
            f'🏠 {response["address"]}' if response["address"] else f"🏠 Not address"
        )

        self.app.menu["Pause Checking"].state = not settings.get_bool("timer_enabled")

        if forced is None or type(forced) == rumps.rumps.Timer:
            self.app.icon = APP_ICON[response["level"]]
            self.app.title = LEVEL_MESSAGE[response["level"]]

        if self.current_level != response["level"] and response["level"]:
            self.send_notification(None)

        self.current_level = response["level"]

    def set_coordinates(self, _):
        """Set address coordinates for monitoring"""
        setting_window = rumps.Window(
            title="Coordinates",
            message=f"Set the coordinates where you want to monitor the air.\n "
            f"Copy the coordinates into Google Maps and paste them here.\n"
            f"For example: 52.23955, 21.045800",
            default_text=f'{settings.get("latitude")}, {settings.get("longitude")}',
            ok="Save",
            cancel="Cancel",
        )

        response = setting_window.run()
        if response.clicked:
            latitude, longitude = (s.strip() for s in str(response.text).split(","))
            settings.set("latitude", latitude)
            settings.set("longitude", longitude)
            settings.save()
            self.refresh_status(None)

    def set_timer_interval(self, _):
        """Set interval in seconds to wait before requesting the Airly API"""
        setting_window = rumps.Window(
            title="Timer",
            message=f"Set interval in minutes to wait before requesting the Airly." f"",
            default_text=f'{int(settings.get("timer_interval")) // 60}',
            ok="Save",
            cancel="Cancel",
            dimensions=(100, 20),
        )
        response = setting_window.run()

        payload = str(response.text).strip()
        if response.clicked and payload.isnumeric():
            timer_interval = int(payload) * 60
            settings.setsave("timer_interval", timer_interval)

            if settings.get_bool("timer_enabled"):
                self.set_timer_activity(False)
                self.timer.interval = timer_interval
                self.set_timer_activity(True)
            else:
                self.timer.interval = timer_interval

    def set_timer_activity(self, status):
        if status:
            self.timer.start()
        else:
            self.timer.stop()
        settings.setsave("timer_enabled", status)
        self.app.menu["Pause Checking"].state = not settings.get_bool("timer_enabled")
        self.app.icon = APP_ICON[""]
        self.app.title = ""

    def switch_timer(self, _):
        self.set_timer_activity(not settings.get_bool("timer_enabled"))

    def send_notification(self, _):
        title = self.app.menu["DESCRIPTION"].title
        subtitle = None
        message = self.app.menu["ADDRESS"].title

        rumps.notification(title, subtitle, message, data=None, sound=True)


if __name__ == "__main__":
    settings.configfile_exists()

    if not settings.has_option("latitude"):
        settings.set("latitude", "52.2394646242")

    if not settings.has_option("longitude"):
        settings.set("longitude", "21.0457174815")

    if not settings.has_option("timer_interval"):
        settings.set("timer_interval", 300)

    if not settings.has_option("timer_enabled"):
        settings.set("timer_enabled", True)

    settings.save()

    app = App()
    app.run()
