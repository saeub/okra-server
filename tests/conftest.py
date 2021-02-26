import pytest

from okra_server.models import Participant


@pytest.fixture(autouse=True)
def database(db):
    pass


@pytest.fixture
def unregistered_participant():
    return Participant.objects.create(
        registration_key="test_regkey",
    )


@pytest.fixture
def registered_participant():
    return Participant.objects.create(
        device_key="test_devkey",
    )
