"""
stripped down version of the original Python test support module
Copyright (c) 2001-2016 Python Software Foundation; All Rights Reserved
"""
# 1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and
#    the Individual or Organization ("Licensee") accessing and otherwise using Python
#    2.7.11 software in source or binary form and its associated documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby
#    grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
#    analyze, test, perform and/or display publicly, prepare derivative works,
#    distribute, and otherwise use Python 2.7.11 alone or in any derivative
#    version, provided, however, that PSF's License Agreement and PSF's notice of
#    copyright, i.e., "Copyright (c) 2001-2016 Python Software Foundation; All Rights
#    Reserved" are retained in Python 2.7.11 alone or in any derivative version
#    prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or
#    incorporates Python 2.7.11 or any part thereof, and wants to make the
#    derivative work available to others as provided herein, then Licensee hereby
#    agrees to include in any such work a brief summary of the changes made to Python
#    2.7.11.
#
# 4. PSF is making Python 2.7.11 available to Licensee on an "AS IS" basis.
#    PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED.  BY WAY OF
#    EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR
#    WARRANTY OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE
#    USE OF PYTHON 2.7.11 WILL NOT INFRINGE ANY THIRD PARTY RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON 2.7.11
#    FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS A RESULT OF
#    MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON 2.7.11, OR ANY DERIVATIVE
#    THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach of
#    its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any relationship
#    of agency, partnership, or joint venture between PSF and Licensee.  This License
#    Agreement does not grant permission to use PSF trademarks or trade name in a
#    trademark sense to endorse or promote products or services of Licensee, or any
#    third party.
#
# 8. By copying, installing or otherwise using Python 2.7.11, Licensee agrees
#    to be bound by the terms and conditions of this License Agreement.

import os
import errno
import unittest
import sys

# Filename used for testing
if os.name == 'java':
    # Jython disallows @ in module names
    TESTFN = '$test'
else:
    TESTFN = '@test'

# Disambiguate TESTFN for parallel testing, while letting it remain a valid
# module name.
TESTFN = "{}_{}_tmp".format(TESTFN, os.getpid())

verbose = 1              # Flag set to 0 by regrtest.py


class BasicTestRunner:
    def run(self, test):
        result = unittest.TestResult()
        test(result)
        return result


class Error(Exception):
    """Base class for regression test exceptions."""


class TestFailed(Error):
    """Test failed."""


def _run_suite(suite):
    """Run tests from a unittest.TestSuite-derived class."""
    if verbose:
        runner = unittest.TextTestRunner(sys.stdout, verbosity=2)
    else:
        runner = BasicTestRunner()

    result = runner.run(suite)
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "multiple errors occurred"
            if not verbose: err += "; run in verbose mode for details"
        raise TestFailed(err)


def run_unittest(*classes):
    """Run tests from unittest.TestCase-derived classes."""
    valid_types = (unittest.TestSuite, unittest.TestCase)
    suite = unittest.TestSuite()
    for cls in classes:
        if isinstance(cls, str):
            if cls in sys.modules:
                suite.addTest(unittest.findTestCases(sys.modules[cls]))
            else:
                raise ValueError("str arguments must be keys in sys.modules")
        elif isinstance(cls, valid_types):
            suite.addTest(cls)
        else:
            suite.addTest(unittest.makeSuite(cls))
    _run_suite(suite)


def findfile(file, here=__file__, subdir=None):
    """Try to find a file on sys.path and the working directory.  If it is not
    found the argument passed to the function is returned (this does not
    necessarily signal failure; could still be the legitimate path)."""
    if os.path.isabs(file):
        return file
    if subdir is not None:
        file = os.path.join(subdir, file)
    path = sys.path
    path = [os.path.dirname(here)] + path
    for dn in path:
        fn = os.path.join(dn, file)
        if os.path.exists(fn): return fn
    return file


def unlink(filename):
    try:
        os.unlink(filename)
    except OSError as error:
        # The filename need not exist.
        if error.errno not in (errno.ENOENT, errno.ENOTDIR):
            raise