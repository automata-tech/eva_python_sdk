from setuptools import setup

setup(
   name='automata',
   version='0.3',
   description='SDK for interacting with the Eva robot',
   author='Automata',
   author_email='ch.c@automata.tech',
   packages=['automata'],
   install_requires=['requests', 'websockets'],
)