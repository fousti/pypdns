from setuptools import setup

from pypdns import __version__

config = {
    'description': 'PowerDNS API python wrapper, library & cli',
    'author': 'Ismael Tifous',
    'url': 'http://github.com/fousti/pypdns',
    'author_email': 'ismael.tifous@gmail.com',
    'version': __version__,
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
