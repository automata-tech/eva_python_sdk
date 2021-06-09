from semver import VersionInfo  # type: ignore
from dataclasses import dataclass

# This is replaced by .github/workflows/publish.yml when creating a release
version = '%VERSION%'

# Use the above version if it has been replaced, otherwise use a dev placeholder
__version__ = version if version.count('%') == 0 else '0.0.dev0'


@dataclass
class EvaVersionRequirements:
    """Supported software versions of the Eva.

    Args:
        min (str): minimum version of Eva's software.
        max (str): maximum version of Eva's software.
    """
    _earliest_eva_supported = '3.0.0'
    _latest_eva_supported = '5.0.0'

    min: str = _earliest_eva_supported
    max: str = _latest_eva_supported

    def message(self) -> str:
        return f'supported Eva versions "{self.min}" to "{self.max}" exclusive'


def sdk_is_compatible_with_robot(eva_version: str) -> str:
    """Checks to see if the current version is compatible with the given version of Eva.

    Args:
        eva_version (str): Eva SemVer version.

    Returns:
        str: An error string if there is one, empty implies compatible.
    """
    eva_requirements = EvaVersionRequirements()
    return compare_version_compatibility(eva_version, eva_requirements)


def compare_version_compatibility(
    eva_version: str,
    eva_requirements: EvaVersionRequirements,
    sdk_version: str = __version__,
) -> str:
    """Checks to see if the given SDK version is compatible with the given software version
    of Eva, in order to decipher the compatibility, we pass in a requirement configuration.
    Pass in sdk_version so that we aren't reliant upon __version__ and thus tests
    don't have to be updated on updating __version__.

    Args:
        eva_version (str): SemVer formated version of Eva software
        eva_requirements (EvaVersionRequirements): Eva version requirements.
        sdk_version (str, optional): SemVer formated version of the SDK. Defaults to __version__.

    Returns:
        str: An error string if there is one, empty implies compatible.
    """
    try:
        VersionInfo.parse(sdk_version)  # checks SemVer validity of SDK version.
        eva_v = VersionInfo.parse(eva_version)
        min_req_satisfied = eva_v.compare(eva_requirements.min) >= 0
        max_req_satisfied = eva_v.compare(eva_requirements.max) < 0
    except ValueError as e:
        return str(e)

    if not max_req_satisfied or not min_req_satisfied:
        return f'Eva is version "{eva_version}". Current SDK version is "{sdk_version}", {eva_requirements.message()}'

    return ''
