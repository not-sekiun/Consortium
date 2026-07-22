# This module raises at import time to exercise the InternalComponentError path.
raise RuntimeError("deliberate module-level import error")
