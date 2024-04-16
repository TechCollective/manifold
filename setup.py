
from setuptools import setup, find_packages
from manifoldcli.core.version import get_version

VERSION = get_version()

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='manifoldcli',
    version=VERSION,
    description='Manifold Connects IT',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Jeffrey Brite',
    author_email='jeff@techcollective.com',
    url='https://github.com/johndoe/myapp/',
    license='GPL v3.0',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'manifoldcli': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        manifoldcli = manifoldcli.main:main
    """,
)
