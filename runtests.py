#!/usr/bin/env python
import os
import sys
import logging
from coverage import coverage
from optparse import OptionParser

from django.conf import settings

from oscar import get_core_apps

logging.disable(logging.CRITICAL)

if not settings.configured:
    print('NO SETTINGS CONFIGURE')
    extra_settings = {
        'AVALARY_RUN_EXTERNAL_TESTS': False,
        'AVALARY_DEVELOPMENT': False,
    }
    print(locals().items())
    print('DONE')
    locals = {key: value for key, value in locals().items() if value}

    from oscar.defaults import *
    for key, value in locals.items():
        if key.startswith('OSCAR'):
            extra_settings[key] = value
    extra_settings['OSCAR_ALLOW_ANON_CHECKOUT'] = True

    from oscar import get_core_apps, OSCAR_MAIN_TEMPLATE_DIR

    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.flatpages',
            'django.contrib.staticfiles',
            'avalara',
        ] + get_core_apps(),
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.transaction.TransactionMiddleware',
            'oscar.apps.basket.middleware.BasketMiddleware',
        ),
        DEBUG=False,
        SOUTH_TESTS_MIGRATE=False,
        HAYSTACK_CONNECTIONS={
            'default': {
                'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
            },
        },
        TEMPLATE_DIRS=(OSCAR_MAIN_TEMPLATE_DIR,),
        SITE_ID=1,
        ROOT_URLCONF='tests.urls',
        COMPRESS_ENABLED=False,
        STATIC_URL='/',
        STATIC_ROOT='.',
        NOSE_ARGS=['-s', '--with-specplugin'],
        **extra_settings
    )


# Needs to be here to avoid missing SETTINGS env var
from django_nose import NoseTestSuiteRunner


def run_tests(*test_args):
    if not test_args:
        test_args = ['tests']

    # Run tests
    test_runner = NoseTestSuiteRunner(verbosity=1)

    c = coverage(source=['avalara'], omit=['*migrations*', '*tests*'])
    c.start()
    num_failures = test_runner.run_tests(test_args)
    c.stop()

    if num_failures > 0:
        sys.exit(num_failures)
    print("Generating HTML coverage report")
    c.html_report()


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
