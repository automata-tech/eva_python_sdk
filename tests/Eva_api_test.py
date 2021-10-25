from evasdk import Eva
import requests_mock


class TestEva_API:
    @requests_mock.Mocker(kw='mock')
    def test_user_agent(self, **kwargs):
        eva = Eva("example.com", "NONE")
        kwargs['mock'].register_uri(
            'GET', 'http://example.com/api/versions',
            request_headers={
                'User-Agent': 'Automata EvaSDK/0.0.dev0 (Python)',
            },
            json={'APIs': ['v1']},
        )
        versions = eva.versions()
        assert(versions['APIs'][0] == 'v1')
