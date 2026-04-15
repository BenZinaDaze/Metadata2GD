"""
zhconv_compat —— 兼容导入 zhconv，并抑制其已知的 pkg_resources 弃用警告。
"""

from __future__ import annotations

import warnings

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=r"pkg_resources is deprecated as an API\.",
        category=UserWarning,
    )
    import zhconv as _zhconv

zhconv = _zhconv

__all__ = ["zhconv"]
