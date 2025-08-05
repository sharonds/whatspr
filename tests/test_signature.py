from app.security import twilio_validator as validator


def test_signature_helper():
    url = "https://example.com/whatsapp"
    params = {"Body": "Hi"}
    sig = validator.compute_signature(url, params)
    assert validator.validate(url, params, sig)
