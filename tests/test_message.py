import pytest
from plin.structs import PLINMessage

@pytest.fixture
def test_message():
    return PLINMessage()

def test_set_message_data(test_message):
    test_message.data = bytearray([0xff])
    assert bytearray(test_message.data) == bytearray([0xff] + [0] * 7)
