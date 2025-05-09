# scripts/lint_plugins.py

import os
import importlib
from manifold_core.secrets.base import SecretBackend

failures = 0
secrets_dir = os.path.join("manifold_core", "secrets")

print("🔍 Validating secret backends...")

for filename in os.listdir(secrets_dir):
    if not filename.endswith(".py") or filename in ("__init__.py", "base.py"):
        continue

    modname = f"manifold_core.secrets.{filename[:-3]}"
    try:
        mod = importlib.import_module(modname)
        cls = getattr(mod, "Backend", None)

        if not cls or not issubclass(cls, SecretBackend):
            print(f"❌ {filename}: Missing or invalid 'Backend' class")
            failures += 1
        elif not hasattr(cls, "get_secret"):
            print(f"❌ {filename}: 'Backend' missing get_secret() method")
            failures += 1
        else:
            print(f"✅ {filename}: OK")
    except Exception as e:
        print(f"❌ {filename}: {e}")
        failures += 1

if failures:
    exit(1)
