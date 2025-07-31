from app.correction import is_correction, extract_correction


def test_correction_star():
    assert is_correction('*Google')
    assert extract_correction('*Google') == 'Google'


def test_correction_imeant():
    msg = 'I meant $3.5M'
    assert is_correction(msg)
    assert extract_correction(msg) == '$3.5M'
