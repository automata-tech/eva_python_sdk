import setuptools  # type: ignore

version = '%VERSION%'  # Replaced by the publish.yml workflow

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='evasdk',
    version=version,
    description='SDK for the Automata Eva robotic arm',
    author='Automata',
    license='Apache License 2.0',
    author_email='louis@automata.tech',
    url="https://github.com/automata-tech/eva_python_sdk",
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'requests',
        'websocket-client',
        'zeroconf',
        'dataclasses',
        'semver',
        # TODO: too big, install it manually if you want it
        # 'pytransform3d',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.6',
)
