
from setuptools import setup

config = {
    'description': 'PowerDNS API python wrapper, library & cli',
    'author': 'Ismael Tifous',
    'url': 'http://github.com/fousti/pypdns',
    'author_email': 'ismael.tifous@gmail.com',
    'version': '0.2',
    'install_requires': ['docopt',
                         'requests'],
    'extras_require': {
        'test': ['nose'],
    },
    'packages': ['pypdns'],
    'name': 'pypdns',
    'entry_points': {
        'console_scripts': [
            'pypdns = pypdns.cli:main'
        ]
     }
}

setup(**config)
