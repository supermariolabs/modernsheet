"""Entry point of the .chs parser: dispatches to the parser of the file's format (see formats/)."""
from __future__ import annotations

from .formats import CURRENT, detect, parse, set_format, upgrade  # noqa: F401
from .formats.v1 import DIRECTIVE_LINE_RE, HALF, TOKEN_RE, split_directive  # noqa: F401
