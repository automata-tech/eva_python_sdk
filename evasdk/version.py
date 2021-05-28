import yaml
from semver import VersionInfo  # type: ignore
from typing import (Dict, Union)

# This is replaced by .github/workflows/publish.yml when creating a release
version = '%VERSION%'

# Use the above version if it has been replaced, otherwise use a dev placeholder
__version__ = version if version.count('%') == 0 else '0.0.dev0'

# Used for version compatibility.
LATEST = 'LATEST'


def sdk_is_compatible_with_robot(sdk_version: str, eva_version: str):
    config = _read_version_compatability()
    if config is None:
        return 'unsupported version: could not read version config file'
    return compare_version_compatability(sdk_version, eva_version, config)


def _read_version_compatability() -> Union[Dict[str, Dict[str, str]], None]:
    with open("version_compatability.yaml", 'r') as stream:
        try:
            version_compatability = yaml.safe_load(stream)
        except yaml.YAMLError:
            return None
    return version_compatability


def compare_version_compatability(
    sdk_version: str,
    eva_version: str,
    version_compatability: Dict[str, Dict[str, str]]
) -> str:
    """Checks to see if the given SDK version is compatible with the given software version of Eva,
    in order to decipher the compatibility, a config map is given. In the map, the key LATEST means
    all and above.

    Args:
        sdk_version (str): SemVer formated version of the SDK
        eva_version (str): SemVer formated version of Eva software
        version_compatability (Dict[str, Dict[str, str]], optional):
            The version compatability map used to decipher whether versions are compatible,
            see default for example.

    Returns:
        str: An error string if there is one, empty str implies given versions
            are compatible.
    """
    try:
        supported_eva = version_compatability[sdk_version]
    except KeyError:
        return f'unsupported version: SDK version "{sdk_version}" does not exist'

    min_eva_version = supported_eva['first_eva']
    max_eva_version = supported_eva['last_eva']

    try:
        eva_v = VersionInfo.parse(eva_version)
        min_req_satisfied = eva_v.compare(min_eva_version) >= 0
        if max_eva_version == LATEST:
            max_req_satisfied = True
        else:
            max_req_satisfied = eva_v.compare(max_eva_version) <= 0
    except ValueError as e:
        return f'unsupported version: {e}'

    compatability_msg = f'SDK version "{sdk_version}" supports Eva versions "{min_eva_version}" to "{max_eva_version}" inclusive'

    if not min_req_satisfied:
        return f'unsupported version: minimum version requirement failure: {compatability_msg}'

    if not max_req_satisfied:
        return f'unsupported version: exceeded version requirement failure: {compatability_msg}'

    return ''
