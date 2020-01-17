#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Declaration:
    Define all BaseError Classes used in aircv.
"""


class BaseError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message=""):
        self.message = message

    def __repr__(self):
        return repr(self.message)


class FileNotExistError(BaseError):
    """Image does not exist."""


class TemplateInputError(BaseError):
    """Resolution input is not right."""


class NoSIFTModuleError(BaseError):
    """Resolution input is not right."""


class NoSiftMatchPointError(BaseError):
    """Exception raised for errors 0 sift points found in the input images."""


class SiftResultCheckError(BaseError):
    """Exception raised for errors 0 sift points found in the input images."""


class HomographyError(BaseError):
    """In homography, find no mask, should kill points which is duplicate."""


class NoModuleError(BaseError):
    """Resolution input is not right."""


class NoMatchPointError(BaseError):
    """Exception raised for errors 0 keypoint found in the input images."""


class MatchResultCheckError(BaseError):
    """Exception raised for errors 0 keypoint found in the input images."""
