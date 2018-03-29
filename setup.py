from setuptools import setup, find_packages
import os

version = '0.0.1'

requires = [
    'setuptools',
]

test_requires = requires + [
    'webtest',
    'python-coveralls==2.5.0',
    'mock==1.0.1',
    'bottle',
    'requests_mock',
    'coverage==3.7.1'
]

docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

api_requires = requires + [
    'openprocurement.api>=2.4',
    'openprocurement.tender.core',
]

entry_points = {
    # 'openprocurement.api.plugins': [
    #     'audit = openprocurement.tender.audit:includeme'
    # ],
    'paste.app_factory': [
        'main = openprocurement.tender.audit:main'
    ],
    # 'openprocurement.api.migrations': [
    #     'audits = openprocurement.tender.audit.migration:migrate_data'
    # ]
}

setup(name='openprocurement.tender.audit',
      version=version,
      description="",
      long_description=open("README.md").read(),
      classifiers=[
        "Framework :: Pylons",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
        ],
      keywords="web services",
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      license='Apache License 2.0',
      url='https://github.com/ITVaan/openprocurement.tender.audit',
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'api': api_requires, 'test': test_requires, 'docs': docs_requires},
      entry_points=entry_points,
      )
