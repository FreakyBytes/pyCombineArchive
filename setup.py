#!/usr/bin/env python

from distutils.core import setup

setup(
    name='pyCombineArchive',
    version='0.0.1',
    license='BSD 3 Clause',
    description='A pure python library to create, modify and read COMBINE Archives',
    author='Martin Peters',
    url='https://github.com/FreakyBytes/pyCombineArchive',
    packages=['combinearchive.combinearchive', 'combinearchive.metadata'],
)