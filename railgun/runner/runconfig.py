#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# @file: railgun/runner/runconfig.py
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Contributors:
#   public@korepwx.com   <public@korepwx.com>
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# This file is released under BSD 2-clause license.

from config import *

## specify the broker of Celery
# NOTE: format of Redis server is redis://:password@hostname:port/db_number
BROKER_URL = 'redis://localhost:6379/0'

## celery run queues
CELERY_DEFAULT_QUEUE = 'default'
CELERY_CREATE_MISSING_QUEUES = True

CELERY_ROUTES = {
    # 'railgun.runner.tasks.helloWorld': {'queue': 'example'}
}

## List of modules to import when celery starts.
CELERY_IMPORTS = ()

## Date and time settings
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_ENABLE_UTC = True

## serialization settings
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']