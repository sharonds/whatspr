from app.validators import validate


def test_money_accept():
    assert validate("f", "$3.5M", "money")[0]


def test_money_reject():
    assert not validate("f", "three", "money")[0]


def test_min_len():
    rule = {"type": "min_len", "min_len": 10}
    assert not validate("h", "short", rule)[0]
    assert validate("h", "long enough answer", rule)[0]
