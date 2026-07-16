"""Imported first by conftest.py, before any src module. Points DATABASE_URL
at a dedicated test database so pytest never touches dev data - src.config's
Settings is a module-level singleton read once at import time, so this has
to run before src.config (or anything importing it) loads."""

import os
import re

from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or re.sub(
    r"/([^/]+)$",
    r"/\1_test",
    os.environ.get(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/mcp_hub"
    ),
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
