import os
import re
from setuptools import setup, find_packages


base_path = os.path.dirname(__file__)

# Get the version (borrowed from SQLAlchemy)
fp = open(os.path.join(base_path, 'lunaport_server', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'",
                     re.S).match(fp.read()).group(1)
fp.close()

setup(
    name='lunaport_server',
    version=VERSION,
    author='Gregory Komissarov',
    author_email='gregory.komissarovv@gmail.com',
    description='HTTP REST APIs service and persistent storage',
    license='BSD',
    url='https://github.domain.org/gkomissarov/lunaport_client',
    keywords=['load', 'lunapark', 'lunaport', 'api'],
    packages=[
        'lunaport_server',
        'lunaport_server.plugg_views',
        'lunaport_server.domain',
        'lunaport_server.dao',
        'lunaport_server.ya',
    ],
    zip_safe=False,
    install_requires=[
       #'requests==1.2.3',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
