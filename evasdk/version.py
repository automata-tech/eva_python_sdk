from packaging import version as p_version
from typing import Dict, Union
import re

# This is replaced by .github/workflows/publish.yml when creating a release
version = '%VERSION%'

# Use the above version if it has been replaced, otherwise use a dev placeholder
__version__ = version if version.count('%') == 0 else '0.0.dev0'

# Used for version compatibility.
LATEST = 'latest'

# Maps SDK version to first and last supported Eva versions.
__EVA_VERSION_COMPATABILITY = {
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
        'last': LATEST
    },
    '4.1.0': {
        'first': '3.0.0',
        'last': LATEST
    },
}


def sdk_is_compatible_with_robot(
    sdk_version: str,
    eva_version: str,
    version_compatability: Dict[str, Dict[str, str]] = __EVA_VERSION_COMPATABILITY
) -> str:
    """Checks to see if the given SDK version is compatible with the given software version of Eva,
    in order to decipher the compatibility, a config map is given. In the map, the key LATEST means
    all and above. Versions are deemed to be legacy by `packaging` if they are not semver compliant.

    Args:
        sdk_version (str): semver formated version of the SDK
        eva_version (str): semver formated version of Eva software
        version_compatability (Dict[str, Dict[str, str]], optional):
            The version compatability map used to decipher whether versions are compatible,
            see default for example. Defaults to __EVA_VERSION_COMPATABILITY.

    Returns:
        str: An error string if there is one, empty str implies given versions
            are compatible.
    """
    try:
        supported_eva = version_compatability[sdk_version]
    except KeyError:
        return f'unsupported version: SDK version "{sdk_version}" does not exist'

    eva = p_version.parse(eva_version)
    if isinstance(eva, p_version.LegacyVersion):
        version = extract_semver(eva_version)
        if version == None:
            return f'unsupported version: Eva version "{eva_version}" is not in semver'
        eva = p_version.parse(eva_version)

    min_eva_version = supported_eva['first']
    max_requirement = supported_eva['last']

    if eva < p_version.parse(min_eva_version):
        return f'unsupported version: SDK version "{sdk_version}" required minimum Eva version "{min_eva_version}"'

    if max_requirement != LATEST and eva > p_version.parse(max_requirement):
        return f'unsupported version: SDK version "{sdk_version}" exceeds the maximum supported Eva version "{max_requirement}"'

    return ''


def extract_semver(version: str) -> Union[str, None]:
    """Takes a version and extracts the semver from it.
    For example '3.1.1-dev-alpha1' would give '3.1.1'.
    If no results are found, returns empty string.

    Args:
        version (str): the str to extract a semver from

    Returns:
        str: semver version stripped of all additional information,
            or None if no results.
    """
    versionPattern = r'\d+(=?\.(\d+(=?\.(\d+)*)*)*)*'
    regexMatcher = re.compile(versionPattern)
    search_results = regexMatcher.search(version)
    if search_results is None:
        return None
    return search_results.group(0)
