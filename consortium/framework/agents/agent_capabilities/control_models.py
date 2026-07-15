from typing import Final

# Stop-signal sentinel returned by a looped capability hook to stop the loop with no
# outcome (a half-close in the streaming capabilities). Authors report a result by
# returning a `Success`/`Failure` directly instead; `None` means "continue".
#
# Compared with `is` so this is a drop-in for the first-class sentinels landing in
# Python 3.15 (PEP 661): when 3.15 releases, only this definition line changes, and the
# `is Finish` checks in the capability engines keep working unchanged.
Finish: Final = object()
