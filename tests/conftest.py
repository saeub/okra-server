import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from okra_server.models import Participant


@pytest.fixture(autouse=True)
def database(db):
    pass


@pytest.fixture(autouse=True, scope="session")
def staticfiles():
    call_command("collectstatic", "--noinput")


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


@pytest.fixture
def authenticated_client(client):
    user = User.objects.create(username="testuser")
    client.force_login(user)
    return client


@pytest.fixture
def staff_authenticated_client(client):
    user = User.objects.create(username="staffuser", is_staff=True)
    client.force_login(user)
    return client
