from app.utils.citations import is_valid_http_url


def test_valid_url():
    assert is_valid_http_url("https://example.com/article")


def test_invalid_url():
    assert not is_valid_http_url("not-a-url")
