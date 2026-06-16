from application.validators.validators import is_valid_email, is_valid_phone


def test_valid_emails():
    assert is_valid_email("a@b.com")
    assert is_valid_email("user.name@nursing.kfs.edu.eg")


def test_invalid_emails():
    assert not is_valid_email("")
    assert not is_valid_email("no-at-sign")
    assert not is_valid_email("a@b")
    assert not is_valid_email("a@@b.com")
    assert not is_valid_email("a b@c.com")


def test_phone():
    assert is_valid_phone("0473221234")
    assert is_valid_phone("+20 47 322-1234")
    assert not is_valid_phone("abc")
    assert not is_valid_phone("123")
