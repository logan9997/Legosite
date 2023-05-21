from setuptools import setup

setup(
    name='project_utils',
    version='0.1',
    description='utility functions to be used throughout the project',
    packages=['project_utils'],
    zip_safe=False,
    install_requires = [
        'scripts', 'config'
    ]
)