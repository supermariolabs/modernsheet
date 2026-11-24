"""Editor support independent of the UI (SPEC §8.2): what changed since the last save, and undo/redo.

- `changes(base, text)`: the parts of `text` that differ from `base` (the text as last saved or
  opened), for the editor to paint their background: whole changed lines lightly, the characters
  actually written strongly.
- `History`: undo / redo steps of a source. Typing is grouped (a word typed, or characters deleted
  one after the other, within GROUP_SECONDS make one step; a space after a word, a new line, a pause,
  a jump of the caret or a different kind of edit start a new one); edits made by the app
  (completion, conversion, format upgrade) are a step of their own.

Standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

LINE, CHARS = 1, 2          # levels of change: a changed line, the characters written in it
GROUP_SECONDS = 1.0
LIMIT = 500                 # undo steps kept


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def changes(base: str, text: str) -> list[tuple[int, int, int]]:
    """(start, end, level) ranges of `text` that differ from `base`, in order and not overlapping:
    LINE over a changed line, CHARS over what was inserted or replaced. Lines that were only
    deleted have nothing to show (undo brings them back)."""
    if base == text:
        return []
    a, b = _lines(base), _lines(text)
    starts = [0]
    for line in b:
        starts.append(starts[-1] + len(line))
    out: list[tuple[int, int, int]] = []
    for op, i1, i2, j1, j2 in SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        if op == "delete":              # whole lines removed: nothing left to paint
            continue
        if op == "insert":
            for j in range(j1, j2):
                out.append((starts[j], starts[j] + len(b[j].rstrip("\n")), CHARS))
            continue
        # replace: characters inside the changed lines
        old, new = "".join(a[i1:i2]), "".join(b[j1:j2])
        base_off = starts[j1]
        marks = [0] * len(new)
        for op2, _, _, k1, k2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
            if op2 in ("replace", "insert"):
                for k in range(k1, k2):
                    marks[k] = CHARS
        for j in range(j1, j2):
            s, e = starts[j] - base_off, starts[j] - base_off + len(b[j].rstrip("\n"))
            for k in range(s, e):
                marks[k] = marks[k] or LINE
        k = 0
        while k < len(marks):
            if not marks[k] or new[k] == "\n":
                k += 1
                continue
            m = k
            while m < len(marks) and marks[m] == marks[k] and new[m] != "\n":
                m += 1
            out.append((base_off + k, base_off + m, marks[k]))
            k = m
    return out


def mark(pieces: list[tuple[str, str]], ranges: list[tuple[int, int, int]]) -> list[tuple[str, str, int]]:
    """Split highlighted pieces (kind, text) at the change ranges: (kind, text, level), level 0 = unchanged."""
    out: list[tuple[str, str, int]] = []
    pos, r = 0, 0
    for kind, s in pieces:
        end = pos + len(s)
        while pos < end:
            while r < len(ranges) and ranges[r][1] <= pos:
                r += 1
            if r < len(ranges) and ranges[r][0] <= pos:
                cut, level = min(end, ranges[r][1]), ranges[r][2]
            else:
                cut, level = min(end, ranges[r][0]) if r < len(ranges) else end, 0
            out.append((kind, s[pos - (end - len(s)):cut - (end - len(s))], level))
            pos = cut
    return out


@dataclass
class _Step:
    before: str
    after: str
    caret_before: int
    caret_after: int
    kind: str               # "insert" (one character), "delete" (one character), "other"
    end: int                # caret after the step, where the next grouped edit must happen
    time: float


class History:
    """Undo and redo of a source text."""

    def __init__(self):
        self.undo_steps: list[_Step] = []
        self.redo_steps: list[_Step] = []

    def clear(self) -> None:
        self.undo_steps.clear()
        self.redo_steps.clear()

    @property
    def can_undo(self) -> bool:
        return bool(self.undo_steps)

    @property
    def can_redo(self) -> bool:
        return bool(self.redo_steps)

    def record(self, old: str, new: str, now: float, group: bool = True) -> None:
        """The text went from `old` to `new` at time `now` (seconds); `group`: may join the last step."""
        if old == new:
            return
        p, n = 0, min(len(old), len(new))
        while p < n and old[p] == new[p]:
            p += 1
        s = 0
        while s < n - p and old[-1 - s] == new[-1 - s]:
            s += 1
        removed, inserted = old[p:len(old) - s], new[p:len(new) - s]
        kind = ("insert" if not removed and len(inserted) == 1 and inserted != "\n" else
                "delete" if not inserted and len(removed) == 1 and removed != "\n" else "other")
        self.redo_steps.clear()
        last = self.undo_steps[-1] if self.undo_steps else None
        if (group and last and kind != "other" and kind == last.kind and last.after == old
                and now - last.time < GROUP_SECONDS):
            # one word (with the spaces that end it) per step
            word_ends = kind == "insert" and inserted in " \t" and old[p - 1:p] not in ("", " ", "\t")
            joined = (p == last.end and not word_ends) if kind == "insert" else (p + 1 == last.end or p == last.end)
            if joined:
                last.after, last.time = new, now
                last.end = last.caret_after = p + 1 if kind == "insert" else p
                return
        end = p + len(inserted)
        self.undo_steps.append(_Step(old, new, p + len(removed), end, kind, end, now))
        del self.undo_steps[:-LIMIT]

    def observe(self, old: str, new: str, now: float) -> str:
        """A change typed in the editor. The text field may undo or redo by itself (its own ⌘Z): a
        change that gives back the text before the last step is taken as that undo, one that gives
        the text after the next redo step as that redo; anything else is recorded. Returns "undo",
        "redo" or "edit"."""
        if self.undo_steps and new == self.undo_steps[-1].before and old == self.undo_steps[-1].after:
            self.redo_steps.append(self.undo_steps.pop())
            return "undo"
        if self.redo_steps and new == self.redo_steps[-1].after and old == self.redo_steps[-1].before:
            self.undo_steps.append(self.redo_steps.pop())
            return "redo"
        self.record(old, new, now)
        return "edit"

    def undo(self) -> tuple[str, int] | None:
        """The text before the last step and the caret to put back; None if there is nothing to undo."""
        if not self.undo_steps:
            return None
        st = self.undo_steps.pop()
        self.redo_steps.append(st)
        return st.before, st.caret_before

    def redo(self) -> tuple[str, int] | None:
        if not self.redo_steps:
            return None
        st = self.redo_steps.pop()
        self.undo_steps.append(st)
        return st.after, st.caret_after
