# This is replaced by .github/workflows/publish.yml when creating a release
version = '%VERSION%'

# Use the above version if it has been replaced, otherwise use a dev placeholder
__version__ = version if version.count('%') == 0 else '0.0.dev0'
