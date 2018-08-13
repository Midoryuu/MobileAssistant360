#!/usr/bin/env python

from setuptools import setup

setup(name='mobile_assistant_360',
      version='0.1',
      description='Python api for downloading application from the Chinese store 360ZhuShou',
      author='Midoryuu',
      author_email='none',
      url='none',
      packages=['mobile_assistant_360'],
      platforms="Linux",
      install_requires=[
          "requests",
          "beautifulsoup4",
          "clint"
      ],
     )