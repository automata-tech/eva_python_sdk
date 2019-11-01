import setuptools

with open("README.md", "r") as fh:
   long_description = fh.read()

setuptools.setup(
   name='eva-sdk',
   version='0.0.1',
   description='SDK for the Automata Eva robotic arm',
   author='Automata',
   license='Apache License 2.0',
   author_email='charlie@automata.tech',
   url="https://github.com/automata-tech/eva_python_sdk",
   packages=setuptools.find_packages(),
   long_description=long_description,
   long_description_content_type="text/markdown",
   install_requires=['requests', 'websockets'],
   classifiers=[
      "Programming Language :: Python :: 3",
      "Development Status :: 4 - Beta",
      "Operating System :: OS Independent",
      "License :: OSI Approved :: Apache Software License",
   ],
   python_requires='>=3.0',
)
