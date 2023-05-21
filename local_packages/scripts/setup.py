from setuptools import setup

setup(
    name='scripts',
    version='0.1',
    description='package containing scripts for api calls, web scraping, database functions',
    packages=['scripts'],
    zip_safe=False,
        install_requires = [
        'scripts', 'project_utils'
    ]
)

