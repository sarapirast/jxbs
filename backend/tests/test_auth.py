from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    new_user_id,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)


def test_verify_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert not verify_password("wrong password", hashed)


def test_hash_password_handles_over_72_bytes_without_crashing():
    # bcrypt only "sees" the first 72 bytes of input
    long_password = "a" * 200
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed)
    assert verify_password("a" * 72, hashed)  # truncated equivalent also matches


def test_new_user_id_is_unique():
    assert new_user_id() != new_user_id()


def test_token_roundtrip():
    token = create_access_token("user-123", "test@example.com")
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "test@example.com"


def test_decode_rejects_garbage_token():
    assert decode_access_token("not-a-real-token") is None


def test_decode_rejects_tampered_token():
    token = create_access_token("user-123", "test@example.com")
    # Flip the last character
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_access_token(tampered) is None
