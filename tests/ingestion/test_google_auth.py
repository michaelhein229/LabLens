from types import SimpleNamespace

import pytest
from google.auth.exceptions import RefreshError

from lablens.ingestion import google_auth


class FakeCredentials:
    def __init__(
        self,
        *,
        valid: bool,
        expired: bool = False,
        refresh_token: str | None = None,
        serialized: str = '{"token": "saved"}',
        refresh_error: Exception | None = None,
    ):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.serialized = serialized
        self.refresh_error = refresh_error
        self.refresh_requests = []

    def refresh(self, request):
        self.refresh_requests.append(request)
        if self.refresh_error:
            raise self.refresh_error
        self.valid = True
        self.expired = False

    def to_json(self):
        return self.serialized


@pytest.fixture
def auth_environment(monkeypatch):
    state = SimpleNamespace(
        token_exists=True,
        loaded_credentials=None,
        browser_credentials=FakeCredentials(
            valid=True,
            serialized='{"token": "browser"}',
        ),
        credential_loads=[],
        flow_creations=[],
        browser_runs=[],
        writes=[],
    )
    state.request = object()
    state.browser_error = None

    monkeypatch.setattr(
        google_auth.os.path,
        "exists",
        lambda path: state.token_exists,
    )

    class FakeCredentialsLoader:
        @staticmethod
        def from_authorized_user_file(path, scopes):
            state.credential_loads.append((path, scopes))
            return state.loaded_credentials

    class FakeFlow:
        def run_local_server(self, port):
            state.browser_runs.append(port)
            if state.browser_error:
                raise state.browser_error
            return state.browser_credentials

    class FakeInstalledAppFlow:
        @staticmethod
        def from_client_secrets_file(path, scopes):
            state.flow_creations.append((path, scopes))
            return FakeFlow()

    class FakeTokenFile:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def write(self, contents):
            state.writes.append(contents)

    def fake_open(path, mode):
        assert path == "secrets/token.json"
        assert mode == "w"
        return FakeTokenFile()

    monkeypatch.setattr(google_auth, "Credentials", FakeCredentialsLoader)
    monkeypatch.setattr(google_auth, "InstalledAppFlow", FakeInstalledAppFlow)
    monkeypatch.setattr(google_auth, "Request", lambda: state.request)
    monkeypatch.setattr("builtins.open", fake_open)

    return state


def test_valid_saved_credentials_return_without_refresh_or_browser(
    auth_environment,
):
    state = auth_environment
    credentials = FakeCredentials(valid=True)
    state.loaded_credentials = credentials

    result = google_auth.get_google_credentials()

    assert result is credentials
    assert state.credential_loads == [
        ("secrets/token.json", google_auth.SCOPES)
    ]
    assert credentials.refresh_requests == []
    assert state.flow_creations == []
    assert state.writes == []


def test_expired_credentials_refresh_and_are_saved(auth_environment):
    state = auth_environment
    credentials = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="refresh-token",
        serialized='{"token": "refreshed"}',
    )
    state.loaded_credentials = credentials

    result = google_auth.get_google_credentials()

    assert result is credentials
    assert credentials.refresh_requests == [state.request]
    assert state.flow_creations == []
    assert state.writes == ['{"token": "refreshed"}']


def test_rejected_refresh_token_runs_browser_authorization(auth_environment):
    state = auth_environment
    expired = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="revoked-token",
        refresh_error=RefreshError("invalid_grant"),
    )
    state.loaded_credentials = expired

    result = google_auth.get_google_credentials()

    assert result is state.browser_credentials
    assert expired.refresh_requests == [state.request]
    assert state.flow_creations == [
        ("secrets/credentials.json", google_auth.SCOPES)
    ]
    assert state.browser_runs == [0]
    assert state.writes == ['{"token": "browser"}']


def test_missing_token_runs_browser_authorization(auth_environment):
    state = auth_environment
    state.token_exists = False

    result = google_auth.get_google_credentials()

    assert result is state.browser_credentials
    assert state.credential_loads == []
    assert state.browser_runs == [0]
    assert state.writes == ['{"token": "browser"}']


def test_unexpected_refresh_error_is_not_hidden(auth_environment):
    state = auth_environment
    credentials = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="refresh-token",
        refresh_error=RuntimeError("network unavailable"),
    )
    state.loaded_credentials = credentials

    with pytest.raises(RuntimeError, match="network unavailable"):
        google_auth.get_google_credentials()

    assert state.flow_creations == []
    assert state.writes == []


def test_failed_browser_authorization_does_not_overwrite_token(
    auth_environment,
):
    state = auth_environment
    state.loaded_credentials = FakeCredentials(
        valid=False,
        expired=True,
        refresh_token="revoked-token",
        refresh_error=RefreshError("invalid_grant"),
    )
    state.browser_error = RuntimeError("authorization cancelled")

    with pytest.raises(RuntimeError, match="authorization cancelled"):
        google_auth.get_google_credentials()

    assert state.writes == []
