"""Hardening tests for the Nuclearn PyP6Xer fork (PR-B).

Two axes:
  1. Decode-safe encoding ladder (no character is ever silently deleted).
  2. Fail-loud typed errors for a malformed value or unroutable structure, a
     soft truncated flag for a file cut before %E, tolerance of short rows,
     and rejoining of P6's quoted tab-containing values on long rows.

Fixtures under tests/fixtures/ are byte-identical to the MRE-side IT-2 corpus.
"""

import codecs
import os

import pytest

from xerparser.exceptions import XerParseError
from xerparser.reader import Reader, _decode_xer_bytes

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


def test_ftb4_short_row_tolerated():
    """A row with fewer fields than its %F header is tolerated like the original
    zip-based parser: trailing columns stay unset and the file is not flagged
    truncated."""
    reader = Reader(fixture("struct_ragged_short.xer"))
    assert len(list(reader.activities)) > 0
    assert reader.truncated is False


def test_ftb4_long_row_raises_field_count():
    """A row longer than its %F header with no quoted span to rejoin fails with
    a field-count error naming table, line and counts, not a conversion error."""
    with pytest.raises(XerParseError) as exc:
        Reader(fixture("struct_ragged_long.xer"))
    assert exc.value.kind == "ragged_row"
    assert exc.value.table == "TASK"
    assert exc.value.line == 83
    assert "expected 60 fields, got 61" in str(exc.value)


def test_ftb4_quoted_tab_value_rejoined(tmp_path):
    """P6 wraps a value containing a tab in double quotes and doubles inner
    quotes. On a too-long row that span is rejoined so later columns stay
    aligned; an unwrapped value with a stray quote is never taken for a span,
    and a row matching its header keeps a bare `""` untouched."""
    content = (
        "ERMHDR\t22.12\t2024-07-29\tProject\n"
        "%T\tTASK\n"
        "%F\ttask_id\ttask_code\ttask_name\tcstr_type\tcstr_type2\ttarget_drtn_hr_cnt\n"
        '%R\t1\tA1\t"Pump\tA ""hot"" test"\t\t\t8\n'
        '%R\t2\tA2\tSay ""hi""\t\t\t4\n'
        '%R\t3\tA3\t"A" train\t6"\t"x\ty"\t2\n'
        "%E\n"
    )
    path = tmp_path / "quoted_tab.xer"
    path.write_text(content, encoding="utf-8")
    tasks = {t.task_code: t for t in Reader(str(path)).activities}
    assert tasks["A1"].task_name == 'Pump\tA "hot" test'
    assert tasks["A1"].target_drtn_hr_cnt == 8.0
    assert tasks["A2"].task_name == 'Say ""hi""'
    assert tasks["A3"].task_name == '"A" train'
    assert tasks["A3"].cstr_type == '6"'
    assert tasks["A3"].cstr_type2 == "x\ty"


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


def test_ftb6_quote_char_in_value_does_not_merge_rows(tmp_path):
    """XER is plain TSV with no quoting convention: a `"` in a value must be a
    literal, not a CSV quote that swallows following rows. Under default csv
    quoting these three rows collapse into one (silent activity loss)."""
    content = (
        "ERMHDR\t8.0\t2021-11-02\tProject\n"
        "%T\tTASK\n"
        "%F\ttask_id\ttask_code\ttask_name\n"
        '%R\t1\tA1\t"Downpower phase\n'
        "%R\t2\tA2\tCooldown to Mode 5\n"
        '%R\t3\tA3\tReactor "trip" test\n'
        "%E\n"
    )
    path = tmp_path / "quotes.xer"
    path.write_text(content, encoding="utf-8")
    reader = Reader(str(path))
    names = task_names(reader)
    assert len(names) == 3
    assert '"Downpower phase' in names
    assert 'Reactor "trip" test' in names


# --- Group 4: decode-ladder rungs (BOM / never-fail floor) --------------------


def test_decode_utf8_bom_stripped():
    """A utf-8 BOM file decodes via the utf-8-sig rung (BOM stripped, text kept)."""
    assert _decode_xer_bytes(codecs.BOM_UTF8 + "café".encode("utf-8")) == "café"


def test_decode_utf16_bom():
    """A utf-16 file (e.g. re-saved through Notepad/Excel) decodes, not mojibake."""
    # str.encode("utf-16") prepends the BOM the ladder sniffs for.
    assert _decode_xer_bytes("café".encode("utf-16")) == "café"


def test_decode_replace_floor_substitutes_never_deletes():
    """A byte undefined in both utf-8 and cp1252 hits the errors='replace' floor."""
    # 0x81 is an invalid utf-8 start byte AND unmapped in strict cp1252.
    assert _decode_xer_bytes(b"\x81") == "�"  # substituted, not deleted; no raise


# --- Group 5: error-message + read-only hygiene -------------------------------


def test_parse_error_message_keeps_line_when_table_unknown():
    """A structural error before any table (empty table) still reports its line."""
    err = XerParseError("ragged_row", "table row missing name", "", 7)
    assert "line 7" in str(err)


def test_get_num_lines_works_on_read_only_file(tmp_path):
    """get_num_lines counts lines without needing write permission on the file."""
    import os

    path = tmp_path / "ro.xer"
    path.write_text("a\nb\nc\n", encoding="utf-8")
    os.chmod(path, 0o444)  # read-only
    reader = object.__new__(Reader)  # bypass __init__; get_num_lines doesn't use self
    assert reader.get_num_lines(str(path)) == 3
