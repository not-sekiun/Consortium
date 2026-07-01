# This module raises at import time to exercise the InternalComponentProjectError path.
raise RuntimeError("deliberate module-level import error")
