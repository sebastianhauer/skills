"""Unit tests for skillkit.frontmatter (the SKILL.md parser).

Loaded via ``load_package`` because the parser lives inside the
``skillkit`` package and uses relative imports.
"""

from __future__ import annotations


def _fm(load_package):
    return load_package("skill-authoring", "skillkit.frontmatter")


def test_happy_path(load_package):
    fm = _fm(load_package)
    text = "---\nname: my-skill\ndescription: Does a thing.\n---\n\n# Body\n"
    fields, violations, body_start = fm.parse_frontmatter(text)
    assert fields == {"name": "my-skill", "description": "Does a thing."}
    assert violations == []
    assert text.split("\n")[body_start] == ""


def test_no_opening_marker(load_package):
    fm = _fm(load_package)
    fields, violations, body_start = fm.parse_frontmatter("name: x\n")
    assert fields == {}
    assert body_start == 0
    assert "does not start with '---'" in violations[0]


def test_no_closing_marker(load_package):
    fm = _fm(load_package)
    fields, violations, body_start = fm.parse_frontmatter("---\nname: x\n")
    assert fields == {}
    assert body_start == 0
    assert "no closing '---'" in violations[0]


def test_quoted_value_is_decoded(load_package):
    fm = _fm(load_package)
    fields, violations, _ = fm.parse_frontmatter('---\ndescription: "Foo: bar"\n---\n')
    assert fields["description"] == "Foo: bar"
    assert violations == []


def test_unquoted_colon_space_is_a_violation(load_package):
    fm = _fm(load_package)
    fields, violations, _ = fm.parse_frontmatter("---\ndescription: Foo: bar\n---\n")
    assert fields["description"] == "Foo: bar"
    assert any("unquoted value containing ': '" in v for v in violations)


def test_block_scalar_is_reconstructed_and_flagged(load_package):
    fm = _fm(load_package)
    text = "---\ndescription: |\n  line one\n  line two\n---\n"
    fields, violations, _ = fm.parse_frontmatter(text)
    assert fields["description"] == "line one line two"
    assert any("block scalar" in v for v in violations)


def test_wrapped_multiline_is_joined_and_flagged(load_package):
    fm = _fm(load_package)
    text = "---\nname: my-skill\n  wrapped\n---\n"
    fields, violations, _ = fm.parse_frontmatter(text)
    assert fields["name"] == "my-skill wrapped"
    assert any("wrapped multiline value" in v for v in violations)


def test_nested_map_ok(load_package):
    fm = _fm(load_package)
    text = "---\nmetadata:\n  short-description: foo\n---\n"
    fields, violations, _ = fm.parse_frontmatter(text)
    assert fields["metadata"] == ""
    assert violations == []


def test_nested_map_empty_is_a_violation(load_package):
    fm = _fm(load_package)
    fields, violations, _ = fm.parse_frontmatter("---\nmetadata:\n---\n")
    assert any("empty value" in v for v in violations)


def test_nested_map_too_deep_is_a_violation(load_package):
    fm = _fm(load_package)
    text = "---\nmetadata:\n  nested:\n    deeper: x\n---\n"
    _, violations, _ = fm.parse_frontmatter(text)
    assert any("single-line scalar" in v for v in violations)


def test_non_key_value_line_is_a_violation(load_package):
    fm = _fm(load_package)
    _, violations, _ = fm.parse_frontmatter("---\nname: x\nnotacolon\n---\n")
    assert any("not a 'key: value' line" in v for v in violations)


def test_unquote_double(load_package):
    fm = _fm(load_package)
    assert fm._unquote('"foo"') == "foo"


def test_unquote_double_escaped(load_package):
    fm = _fm(load_package)
    assert fm._unquote('"a\\"b"') == 'a"b'


def test_unquote_single(load_package):
    fm = _fm(load_package)
    assert fm._unquote("'foo'") == "foo"


def test_unquote_single_doubled(load_package):
    fm = _fm(load_package)
    assert fm._unquote("'it''s'") == "it's"


def test_unquote_plain(load_package):
    fm = _fm(load_package)
    assert fm._unquote("foo") == "foo"


def test_is_indented(load_package):
    fm = _fm(load_package)
    assert fm.is_indented(" x")
    assert fm.is_indented("\tx")
    assert not fm.is_indented("x")
    assert not fm.is_indented("")
