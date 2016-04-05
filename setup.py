#!/usr/bin/env python

from distutils.core import setup
from setuptools import find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pyCombineArchive',
    version='0.1.0.dev1',
    license='BSD 3 Clause',
    description='A pure python library to create, modify and read COMBINE Archives',
    long_description=long_description,
    author='Martin Peters',
    url='https://github.com/FreakyBytes/pyCombineArchive',
    packages=find_packages(exclude=['tests*']),
)