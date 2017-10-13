#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Declaration:
    Define all Error Classes used in aircv.py.
"""


class Error(Exception):
    """Base class for exceptions in this module."""

    pass


class InvalidImageInputError(Error):
    """Image file not exist."""

    def __init__(self, message):
        """Init."""
        self.message = message


class TemplateInputError(Error):
    """Resolution input is not right."""

    def __init__(self, message):
        """Init."""
        self.message = message


class PredictAreaNoneError(Error):
    """Resolution input is not right."""

    def __init__(self, message):
        """Init."""
        self.message = message


class NoneGoodError(Error):
    """After sift, find no good points."""

    def __init__(self, message):
        """Init."""
        self.message = message


class NoSIFTModuleError(Error):
    """Resolution input is not right."""

    def __init__(self, message):
        """Init."""
        self.message = message


class NoSiftMatchPointError(Error):
    """Exception raised for errors 0 sift points found in the input images.

    Attributes:
        message -- explanation of the error.
    """

    def __init__(self, message):
        """Init."""
        self.message = message


class SiftResultCheckError(Error):
    """Exception raised for errors 0 sift points found in the input images.

    Attributes:
        message -- explanation of the error.
    """

    def __init__(self, message):
        """Init."""
        self.message = message


class HomographyError(Error):
    """In homography, find no mask, should kill points which is duplicate."""

    def __init__(self, message):
        """Init."""
        self.message = message


class InvalidCropTargetError(Error):
    """Image file not exist."""

    def __init__(self, message):
        """Init."""
        self.message = message
