"""Fast release-boundary tests, independent of the application database.

Run from backend: python tools/run_mvp_scope_tests.py
This does not replace the application integration suite.
"""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from django.conf import settings

settings.configure(
    SECRET_KEY="isolated-mvp-test", DATABASES={}, INSTALLED_APPS=[],
    DEFAULT_CHARSET="utf-8",
)
import django

django.setup()
suite = unittest.defaultTestLoader.loadTestsFromName("core_apps.common.tests_mvp_scope")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
