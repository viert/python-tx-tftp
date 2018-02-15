"""Installer for python-tx-tftp."""

from setuptools import setup, find_packages


setup(
    name='python-tx-tftp',
    author='Shylent',
    author_email='-',
    url='https://github.com/shylent/python-tx-tftp',
    version="0.2",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
    packages=find_packages(),
    install_requires=["Twisted"],
    description="A Twisted-based TFTP implementation.",
    setup_requires=["setuptools_trial"],
    test_suite="tftp",
)
