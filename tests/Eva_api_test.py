from evasdk import Eva


class TestEva_API:
    def test_user_agent(self, requests_mock):
        eva = Eva("example.com", "NONE")

        requests_mock.register_uri(
            'GET', 'http://example.com/api/versions',
            request_headers={
                'User-Agent': 'Automata EvaSDK/0.0.dev0 (Python)',
            },
            json={'APIs': ['v1']},
        )
        versions = eva.versions()
        assert(versions['APIs'][0] == 'v1')
