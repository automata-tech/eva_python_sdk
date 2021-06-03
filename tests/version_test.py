from evasdk.version import (compare_version_compatibility, EvaVersionRequirements)

import pytest


@pytest.mark.parametrize('sdk_version,eva_version,eva_version_support,want_error', [
    (
        '234134',
        '3.0.0',
        EvaVersionRequirements(min='1.0.0', max='2.0.0'),
        'unsupported version: 234134 is not valid SemVer string'
    ),
    (
        '1.0.0',
        'latest',
        EvaVersionRequirements(min='1.0.0', max='2.0.0'),
        'unsupported version: latest is not valid SemVer string'
    ),
    (
        '1.0.0',
        '2.0.0',
        EvaVersionRequirements(min='2.0.0',max='2.1.0'),
        ''
    ),
    (
        '1.0.0',
        '2.1.0',
        EvaVersionRequirements(min='2.0.0',max='2.1.0'),
        'unsupported version: exceeded version requirement failure: SDK version "1.0.0" supports Eva versions "2.0.0" to "2.1.0" exclusive'
    ),
    (
        '1.0.0',
        '2.1.4',
        EvaVersionRequirements(min='2.0.0',max='2.1.0'),
        'unsupported version: exceeded version requirement failure: SDK version "1.0.0" supports Eva versions "2.0.0" to "2.1.0" exclusive'
    ),
    (
        '3.0.0',
        '3.6.0',
        EvaVersionRequirements(min='3.1.0',max='3.1.0'),
        'unsupported version: exceeded version requirement failure: SDK version "3.0.0" supports Eva versions "3.1.0" to "3.1.0" exclusive'
    ),
    (
        '3.0.0',
        '3.1.0-dev-tet',
        EvaVersionRequirements(min='3.1.0',max='3.1.0'),
        'unsupported version: minimum version requirement failure: SDK version "3.0.0" supports Eva versions "3.1.0" to "3.1.0" exclusive'
    ),
    (
        '1.0.0',
        '2.1.1-dev-test',
        EvaVersionRequirements(min='2.0.0',max='2.1.2'),
        ''
    ),
    (
        '3.0.0',
        'not-a-version',
        EvaVersionRequirements(min='2.0.0',max='2.1.2'),
        'unsupported version: not-a-version is not valid SemVer string'
    ),
])
def test_compare_version_compatibility(sdk_version, eva_version, eva_version_support, want_error):
    err = compare_version_compatibility(eva_version, eva_version_support, sdk_version=sdk_version)
    assert err == want_error

