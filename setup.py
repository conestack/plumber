from setuptools import find_packages
from setuptools import setup
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '1.7.dev0'
shortdesc = 'An alternative to mixin-based extension of classes.'
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'LICENSE.rst'
]])


setup(
    name='plumber',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    keywords='class extension mixin alternative',
    author='Node Contributors',
    author_email='dev@conestack.org',
    url='http://github.com/conestack/plumber',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=True,
    install_requires=['setuptools'],
    extras_require=dict(test=['zope.interface']),
    test_suite='plumber.tests',
    entry_points="""
    """
)
