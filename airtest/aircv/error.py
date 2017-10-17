#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Declaration:
    Define all BaseError Classes used in aircv.py.
"""


class BaseError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message=""):
        self.message = message


class InvalidImageInputError(BaseError):
    """Image file not exist."""
    pass


class TemplateInputError(BaseError):
    """Resolution input is not right."""
    pass


class PredictAreaNoneError(BaseError):
    """Resolution input is not right."""
    pass


class NoSiftFeatureMatched(BaseError):
    """After sift, find no good points."""
    pass


class NoSIFTModuleError(BaseError):
    """Resolution input is not right."""
    pass


class NoSiftMatchPointError(BaseError):
    """Exception raised for errors 0 sift points found in the input images."""
    pass


class SiftResultCheckError(BaseError):
    """Exception raised for errors 0 sift points found in the input images."""
    pass


class HomographyError(BaseError):
    """In homography, find no mask, should kill points which is duplicate."""
    pass


class InvalidCropTargetError(BaseError):
    """Image file not exist."""
    pass
