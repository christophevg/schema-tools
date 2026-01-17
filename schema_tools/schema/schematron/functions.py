"""
Schematron uses custom XSLT functions within its XSLT patterns. Unfortunately, there isn’t a readily available package that supports such in-XML defined custom functions. This module addresses this issue by implementing these functions in plain Python and injecting them into the parser, enabling the parser to utilize these functions.

It’s important to note that stubs for all functions in the PEPPOL-EN16931-UBL Schematron are generated here below. However, only a few (one? ;-)) of these functions have been actually implemented. When these functions are not implemented and are used during validation, a warning is logged.
"""

# ruff: noqa: F841

from elementpath.xpath3 import XPath3Parser

import logging
logger = logging.getLogger(__name__)

method = XPath3Parser.method
function = XPath3Parser.function

@method(function("mod97-0208", nargs=1,
        sequence_types=('xs:string?', 'xs:boolean')))
def evaluate_mod97_0208_function(self, context):
  """
  The `mod97-0208 function calculates the remainder when the first part of the input is divided by 97 and compares it to the expected complement of the remainder, which is represented by the last two characters.
  """
  if self.context is not None:
      context = self.context
  string: str = self.get_argument(context, default='', cls=str)
  number = int(string[:-2]) # everything up to the last two chars
  mod    = int(string[-2:]) # the last two chars
  return 97 - (number % 97) == mod

@method(function("slack", nargs=3,
  sequence_types=('xs:decimal', 'xs:decimal', 'xs:decimal', 'xs:boolean')))
def evaluate_slack_function(self, context):
  if self.context is not None:
      context = self.context
  exp = self.get_argument(context, default=0.0, cls=(float,int))
  val = self.get_argument(context, default=0.0, cls=(float,int))
  slack = self.get_argument(context, default=0.0, cls=(float,int))
  return (exp + slack) >= val and (exp - slack) <= val

# below are stubs of functions without implementation
# many of these are not (yet) applicable

@method(function("gln", nargs=1,
  sequence_types=('xs:anyAtomicType?', 'xs:boolean')))
def evaluate_gln_function(self, context):
  if self.context is not None:
      context = self.context
  val = self.get_argument(context, default='', cls=str)
  logger.warning("function 'gln' hasn't been implemented yet!")
  return True

@method(function("mod11", nargs=1,
  sequence_types=('xs:anyAtomicType?', 'xs:boolean')))
def evaluate_mod11_function(self, context):
  if self.context is not None:
      context = self.context
  val = self.get_argument(context, default='', cls=str)
  logger.warning("function 'mod11' hasn't been implemented yet!")
  return True

@method(function("checkCodiceIPA", nargs=1,
  sequence_types=('xs:string?', 'xs:boolean')))
def evaluate_checkCodiceIPA_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkCodiceIPA' hasn't been implemented yet!")
  return True

@method(function("checkCF", nargs=1,
  sequence_types=('xs:string?', 'xs:boolean')))
def evaluate_checkCF_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkCF' hasn't been implemented yet!")
  return True

@method(function("checkCF16", nargs=1,
  sequence_types=('xs:string?', 'xs:boolean')))
def evaluate_checkCF16_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkCF16' hasn't been implemented yet!")
  return True

@method(function("checkPIVAseIT", nargs=1,
  sequence_types=('xs:string', 'xs:boolean')))
def evaluate_checkPIVAseIT_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkPIVAseIT' hasn't been implemented yet!")
  return True

@method(function("checkPIVA", nargs=1,
  sequence_types=('xs:string?', 'xs:integer')))
def evaluate_checkPIVA_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkPIVA' hasn't been implemented yet!")
  return True

@method(function("addPIVA", nargs=2,
  sequence_types=('xs:string', 'xs:integer', 'xs:integer')))
def evaluate_addPIVA_function(self, context):
  if self.context is not None:
      context = self.context
  arg = self.get_argument(context, default='', cls=str)
  pari = self.get_argument(context, default=0, cls=int)
  logger.warning("function 'addPIVA' hasn't been implemented yet!")
  return True

@method(function("abn", nargs=1,
  sequence_types=('xs:anyAtomicType?', 'xs:boolean')))
def evaluate_abn_function(self, context):
  if self.context is not None:
      context = self.context
  val = self.get_argument(context, default='', cls=str)
  logger.warning("function 'abn' hasn't been implemented yet!")
  return True

@method(function("TinVerification", nargs=1,
  sequence_types=('xs:string', 'xs:boolean')))
def evaluate_TinVerification_function(self, context):
  if self.context is not None:
      context = self.context
  val = self.get_argument(context, default='', cls=str)
  logger.warning("function 'TinVerification' hasn't been implemented yet!")
  return True

@method(function("checkSEOrgnr", nargs=1,
  sequence_types=('xs:string', 'xs:boolean')))
def evaluate_checkSEOrgnr_function(self, context):
  if self.context is not None:
      context = self.context
  number = self.get_argument(context, default='', cls=str)
  logger.warning("function 'checkSEOrgnr' hasn't been implemented yet!")
  return True
