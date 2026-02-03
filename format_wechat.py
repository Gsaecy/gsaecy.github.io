"""Import shim for format-wechat.py (hyphenated filename).

Allows other scripts to do:
  from format_wechat import WeChatFormatter
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_here = Path(__file__).resolve().parent
_src = _here / "format-wechat.py"

spec = importlib.util.spec_from_file_location("format_wechat_impl", _src)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load {_src}")

mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[attr-defined]

WeChatFormatter = mod.WeChatFormatter
