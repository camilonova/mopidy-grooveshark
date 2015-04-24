from __future__ import unicode_literals

import re
from setuptools import setup, find_packages


def get_version(filename):
    content = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
    return metadata['version']


setup(
    name='Mopidy-Grooveshark',
    version=get_version('mopidy_grooveshark/__init__.py'),
    url='https://github.com/camilonova/mopidy-grooveshark',
    license='MIT',
    author='Camilo Nova',
    author_email='camilo.nova@gmail.com',
    description='Mopidy extension that plays sound from Grooveshark',
    long_description=open('README.md').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
    ],
    entry_points={
        'mopidy.ext': [
            'grooveshark = mopidy_grooveshark:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
