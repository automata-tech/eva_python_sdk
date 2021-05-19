from evasdk.version import (sdk_is_compatible_with_robot, extract_semver)

import pytest


test_version_map = {
    '1.0.0': {
        'first': '2.0.0',
        'last': '2.1.2',
    },
    '2.0.0': {
        'first': '3.0.0',
        'last': '3.0.1',
    },
    '3.0.0': {
        'first': '3.1.0',
        'last': '3.1.0',
    },
    '4.0.0': {
        'first': '3.0.0',
        'last': 'latest'
    },
    '4.1.0': {
        'first': '3.0.0',
        'last': 'latest'
    },
}


@pytest.mark.parametrize('sdk_version,eva_version,want_error', [
    (
        '234134',
        '3.0.0',
        'unsupported version: SDK version "234134" does not exist'
    ),
    (
        '1.0.0',
        'latest',
        'unsupported version: Eva version "latest" is not in semver'
    ),
    (
        '1.0.0',
        '2.0.0',
        ''
    ),
    (
        '1.0.0',
        '2.1.0',
        ''
    ),
    (
        '1.0.0',
        '2.1.2',
        ''
    ),
    (
        '1.0.0',
        '2.1.4',
        'unsupported version: SDK version "1.0.0" exceeds the maximum supported Eva version "2.1.2"'
    ),
    (
        '4.0.0',
        '4.6.0',
        ''
    ),
    (
        '3.0.0',
        '3.6.0',
        'unsupported version: SDK version "3.0.0" exceeds the maximum supported Eva version "3.1.0"'
    ),
    (
        '3.0.0',
        '3.9.0-dev-tet',
        'unsupported version: SDK version "3.0.0" required minimum Eva version "3.1.0"'
    ),
    (
        '3.0.0',
        'not-a-version',
        'unsupported version: Eva version "not-a-version" is not in semver'
    ),
])
def test_sdk_is_compatible_with_robot(sdk_version, eva_version, want_error):
    err = sdk_is_compatible_with_robot(sdk_version, eva_version, test_version_map)
    assert err == want_error



@pytest.mark.parametrize('input,expected', [
    ('3.3.3', '3.3.3'),
    ('13.33.43', '13.33.43'),
    ('13.33.43a', '13.33.43'),
    ('13.33.43-development', '13.33.43'),
    ('13.33.43-testing-alpha123', '13.33.43'),
    ('latest', ''),
    ('new', ''),
    ('', ''),
])
def test_extract_semver(input, expected):
    got = extract_semver(input)
    assert got == expected
