# -*- encoding: utf-8 -*-
"""
    lunaport.dao.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~

    Common for all storage operations exception.
"""


class StorageError(Exception):
    def __init__(self, msg, orig_e=None, missing_resource_type=None,
                 missing_resource_value=None):
        self.orig_e = orig_e
        self.msg = msg
        self.missing_resource_type = missing_resource_type
        self.missing_resource_value = missing_resource_value

    def __str__(self):
        return repr(self.msg)
