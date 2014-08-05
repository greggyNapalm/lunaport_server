#!/usr/bin/env python

"""
    check_versions_consistency
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Script called via Makefile to verify that `debian/changelog`, pythom module
    and `CHANGES.rst` have tha same version.
"""

import os
import sys
import re

APP_MODULE_PATH = 'lunaport_server/__init__.py'
DEB_CHANGELOG_PATH = 'debian/changelog'

def get_py_module_version(path=APP_MODULE_PATH):
    with open(path, 'r') as fh:
        return re.compile(r".*__version__ = '(.*?)'",
                          re.S).match(fh.read()).group(1)

def get_deb_changelog_version(path=DEB_CHANGELOG_PATH):
    return open(path, 'r').readline().split(' ')[1].lstrip('(').rstrip(')')


def main():
    print get_py_module_version() == get_deb_changelog_version(),

if __name__ == '__main__':
    main()
