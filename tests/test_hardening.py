"""Hardening tests for the Nuclearn PyP6Xer fork (PR-B).

Two axes:
  1. Decode-safe encoding ladder (no character is ever silently deleted).
  2. Fail-loud typed parse errors for structural corruption (bad / ragged /
     truncated), plus a per-Reader reset of the class-level obj_lists.

Fixtures under tests/fixtures/ are byte-identical to the MRE-side IT-2 corpus.
"""

import os

import pytest

from xerparser.exceptions import XerParseError
from xerparser.model.classes.taskpred import TaskPred
from xerparser.model.classes.wbs import WBS
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


# --- Group 2: typed parse errors (FT-B3 / FT-B4 / FT-B5) ----------------------


def test_ftb3_bad_row_raises_malformed():
    """A non-numeric task_id raises a typed malformed_row error with location."""
    with pytest.raises(XerParseError) as exc:
        Reader(fixture("struct_bad_row_raises.xer"))
    assert exc.value.kind == "malformed_row"
    assert exc.value.table == "TASK"
    assert exc.value.line  # a concrete line number, not None


@pytest.mark.parametrize("name", ["struct_ragged_short.xer", "struct_ragged_long.xer"])
def test_ftb4_ragged_row_raises(name):
    """A row whose field count != its %F header raises a typed ragged_row error."""
    with pytest.raises(XerParseError) as exc:
        Reader(fixture(name))
    assert exc.value.kind == "ragged_row"
    assert exc.value.table == "TASK"


def test_ftb5_truncated_sets_flag_and_keeps_rows():
    """A file cut off mid-row parses without raising, flags truncated, and keeps
    the valid rows before the cut."""
    reader = Reader(fixture("struct_truncated_midrow.xer"))
    assert reader.truncated is True
    assert len(list(reader.activities)) > 0


def test_ftb5_golden_parses_clean():
    """The false-positive control: a complete clean file raises nothing and is
    not flagged truncated."""
    reader = Reader(fixture("golden.xer"))
    assert len(list(reader.activities)) > 0
    assert reader.truncated is False


# --- Group 3: per-Reader obj_list reset (FT-B7) -------------------------------


def test_ftb7_objlist_reset_between_readers():
    """A second Reader resets the class-level WBS/TaskPred lists (no bleed)."""
    Reader(fixture("golden.xer"))
    Reader(fixture("enc_utf8_cjk.xer"))
    # Sized to the second file alone (each clean mini file: 10 WBS / 19 preds);
    # accumulation across Readers would give 20 / 38.
    assert len(WBS.obj_list) == 10
    assert len(TaskPred.obj_list) == 19
