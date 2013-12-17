# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='maxcube',
    version='0.0.1',
    description='Python API to Max Cube ELV',
    long_description=readme,
    author='Ales Zoulek',
    author_email='ales.zoulek@gmail.com',
    url='https://github.com/aleszoulek/maxcube',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points = {
        'console_scripts': [
            'maxcube = maxcube.scripts.main:main',
        ],
    },
    test_suite = 'nose.collector',
    classifiers = [
        "Development Status :: 4 - Beta",
        "Programming Language :: Python",
        "Operating System :: OS Independent",
    ],
)
