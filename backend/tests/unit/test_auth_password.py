from app.auth.password import hash_password, verify_password


def test_argon2_hash_and_verify():
    hashed = hash_password("test-password-123")
    assert verify_password(hashed, "test-password-123")
    assert not verify_password(hashed, "wrong")
