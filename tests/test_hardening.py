"""Hardening tests for the Nuclearn PyP6Xer fork (PR-B).

Two axes:
  1. Decode-safe encoding ladder (no character is ever silently deleted).
  2. Fail-loud typed parse errors for structural corruption (bad / ragged /
     truncated), plus a per-Reader reset of the class-level obj_lists.

Fixtures under tests/fixtures/ are byte-identical to the MRE-side IT-2 corpus.
"""

import os

from xerparser.reader import Reader

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def fixture(name):
    return os.path.join(FIXTURES, name)


def task_names(reader):
    return [t.task_name or "" for t in reader.activities]


# --- Group 1: encoding ladder (FT-B1 / FT-B2) ---------------------------------


def test_ftb1_cp1252_accents_survive():
    """cp1252 accented task names decode via the cp1252 rung (was deleted)."""
    reader = Reader(fixture("enc_cp1252_accents.xer"))
    non_ascii = [c for n in task_names(reader) for c in n if ord(c) > 127]
    assert sorted(set(non_ascii)) == sorted({"é", "°", "Æ"})
    assert len(non_ascii) == 6


def test_ftb2_utf8_cjk_survive():
    """utf-8 CJK names survive untouched — pins utf-8-first ordering."""
    reader = Reader(fixture("enc_utf8_cjk.xer"))
    names = task_names(reader)
    cjk = [c for n in names for c in n if ord(c) > 127]
    assert len(cjk) == 12
    # cp1252-always would mangle each 3-byte CJK char into 3 Latin glyphs.
    assert "反" in "".join(names)
