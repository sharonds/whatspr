from app.validators import validate


def test_money():
    ok, _ = validate("fund", "$3.5M", "money")
    assert ok
    bad, _ = validate("fund", "three", "money")
    assert not bad
