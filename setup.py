from codecs import open
from os import path
from setuptools import setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    readme = f.read()

with open(path.join(here, 'requirements', 'install.txt'),
          encoding='utf-8') as f:
    install_requires = f.read().splitlines()

setup(
    name='analyzere',
    version='0.5.2',
    description='Python wrapper for the Analyze Re API.',
    long_description=readme,
    url='https://github.com/analyzere/analyzere-python',
    author='Analyze Re',
    author_email='support@analyzere.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=[
        'analyzere',
    ],
    install_requires=install_requires
)
