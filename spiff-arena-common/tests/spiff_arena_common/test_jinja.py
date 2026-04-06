from spiff_arena_common.jinja import jinja


def test_successful_render():
    template = "Hello {{ name }}"
    result, error = jinja(template, {"name": "Dan"})
    assert result == "Hello Dan"
    assert error is None


def test_syntax_error_includes_line_info():
    template = "Line one\n{% if %}\nLine three"
    result, error = jinja(template, {})
    assert result is None
    assert "TemplateSyntaxError" in error
    assert "Line 2" in error
    assert "{% if %}" in error


def test_undefined_variable_with_tojson_returns_error():
    template = "Line one\nThe data is {{ undefined_var | tojson }}\nLine three"
    result, error = jinja(template, {})
    assert result is None
    assert error is not None
    assert "undefined_var" in error
