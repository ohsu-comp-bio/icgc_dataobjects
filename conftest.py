#!/usr/bin/env python
"""
configure tests - returns a reference to the app
"""

from icgc_dataobjects import run
import pytest
import os
from json import dumps


@pytest.fixture
def app(request):
    # get app from main
    app = run.app
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()
