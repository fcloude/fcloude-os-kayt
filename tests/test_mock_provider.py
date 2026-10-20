from kayt.providers.mock import MockProvider


def test_mock_provider_returns_predictable_response():
    provider = MockProvider()
    assert provider.respond("anything at all") == "mock response"


def test_mock_provider_reports_its_name():
    assert MockProvider().name == "mock"
