"""WSGI entry point used by PythonAnywhere."""

import os

os.environ.setdefault("AUTO_CREATE_DB", "0")
os.environ.setdefault("SEED_DEMO_DATA", "0")

from app import create_app


application = create_app()