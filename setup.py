from setuptools import setup

APP = ['QAirMon.py']
DATA_FILES = [('', ['data'])]
OPTIONS = {
    # 'argv_emulation': True,
    'plist': {
        'LSUIElement': True,
    },
    'iconfile':'data/app.png',
    # 'packages': ['rumps', 'requests'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)