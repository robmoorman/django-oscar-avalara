#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

setup(name='django-oscar-avalara',
      version='0.2.1',
      url='https://github.com/django-oscar/django-oscar-avalara',
      author="David Winterbottom",
      author_email="david.winterbottom@gmail.com",
      description="Avalara integration for django-oscar",
      long_description=open('README.rst').read(),
      keywords="Taxes, Avalara",
      license='BSD',
      packages=find_packages(exclude=['sandbox*', 'tests*']),
      include_package_data=True,
      install_requires=[
          'django>=1.8.8,<1.12',
          'django-oscar>=1.3,<1.5',
          'requests',
          'purl>=1.3.1,<1.4',
      ],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Unix',
          'Programming Language :: Python']
      )
