from evasdk.version import (compare_version_compatability, sdk_is_compatible_with_robot)

import pytest


test_version_map = {
    '1.0.0': {
        'first_eva': '2.0.0',
        'last_eva': '2.1.2',
    },
    '2.0.0': {
        'first_eva': '3.0.0',
        'last_eva': '3.0.1',
    },
    '3.0.0': {
        'first_eva': '3.1.0',
        'last_eva': '3.1.0',
    },
    '4.0.0': {
        'first_eva': '3.0.0',
        'last_eva': 'LATEST'
    },
    '4.1.0': {
        'first_eva': '3.0.0',
        'last_eva': 'LATEST'
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
        'unsupported version: latest is not valid SemVer string'
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
        'unsupported version: exceeded version requirement failure: SDK version "1.0.0" supports Eva versions "2.0.0" to "2.1.2" inclusive'
    ),
    (
        '4.0.0',
        '4.6.0',
        ''
    ),
    (
        '3.0.0',
        '3.6.0',
        'unsupported version: exceeded version requirement failure: SDK version "3.0.0" supports Eva versions "3.1.0" to "3.1.0" inclusive'
    ),
    (
        '3.0.0',
        '3.9.0-dev-tet',
        'unsupported version: exceeded version requirement failure: SDK version "3.0.0" supports Eva versions "3.1.0" to "3.1.0" inclusive'
    ),
    (
        '1.0.0',
        '2.1.1-dev-test',
        ''
    ),
    (
        '1.0.0',
        '2.1.2-dev-test',
        ''
    ),
    (
        '3.0.0',
        'not-a-version',
        'unsupported version: not-a-version is not valid SemVer string'
    ),
])
def test_compare_version_compatability(sdk_version, eva_version, want_error):
    err = compare_version_compatability(sdk_version, eva_version, test_version_map)
    assert err == want_error


def test_sdk_is_compatible_with_robot():
    # this tests the version_compatability file is correctly loaded and checked against.
    compatible = sdk_is_compatible_with_robot("1.0.0", "2.0.0")
    assert compatible == ""
