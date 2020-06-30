import setuptools
from evasdk.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='evasdk',
    version=__version__,
    description='SDK for the Automata Eva robotic arm',
    author='Automata',
    license='Apache License 2.0',
    author_email='charlie@automata.tech',
    url="https://github.com/automata-tech/eva_python_sdk",
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'requests',
        'websockets',
        'zeroconf',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.0',
)
