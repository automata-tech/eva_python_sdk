from evasdk.version import (compare_version_compatibility, EvaVersionRequirements)

import pytest


@pytest.mark.parametrize('sdk_version,eva_version,eva_version_support,want_error', [
    (
        '234134',
        '3.0.0',
        EvaVersionRequirements(min='1.0.0', max='2.0.0'),
        '234134 is not valid SemVer string'
    ),
    (
        '1.0.0',
        'latest',
        EvaVersionRequirements(min='1.0.0', max='2.0.0'),
        'latest is not valid SemVer string'
    ),
    (
        '1.0.0',
        '2.0.0',
        EvaVersionRequirements(min='2.0.0', max='2.1.0'),
        None
    ),
    (
        '1.0.0',
        '2.1.0',
        EvaVersionRequirements(min='2.0.0', max='2.1.0'),
        'Eva is version "2.1.0". Current SDK version is "1.0.0", supported Eva versions "2.0.0" to "2.1.0" exclusive'
    ),
    (
        '1.0.0',
        '2.1.4',
        EvaVersionRequirements(min='2.0.0', max='2.1.0'),
        'Eva is version "2.1.4". Current SDK version is "1.0.0", supported Eva versions "2.0.0" to "2.1.0" exclusive'
    ),
    (
        '3.0.0',
        '3.6.0',
        EvaVersionRequirements(min='3.1.0', max='3.1.0'),
        'Eva is version "3.6.0". Current SDK version is "3.0.0", supported Eva versions "3.1.0" to "3.1.0" exclusive'
    ),
    (
        '3.0.0',
        '3.1.0-dev-tet',
        EvaVersionRequirements(min='3.1.0', max='3.1.0'),
        'Eva is version "3.1.0-dev-tet". Current SDK version is "3.0.0", supported Eva versions "3.1.0" to "3.1.0" exclusive'
    ),
    (
        '1.0.0',
        '2.1.1-dev-test',
        EvaVersionRequirements(min='2.0.0', max='2.1.2'),
        None
    ),
    (
        '3.0.0',
        'not-a-version',
        EvaVersionRequirements(min='2.0.0', max='2.1.2'),
        'not-a-version is not valid SemVer string'
    ),
])
def test_compare_version_compatibility(sdk_version, eva_version, eva_version_support, want_error):
    err = compare_version_compatibility(eva_version, eva_version_support, sdk_version=sdk_version)
    assert err == want_error
