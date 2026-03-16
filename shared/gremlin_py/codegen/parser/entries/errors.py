# Protocol Buffer parser error types and utilities.
# This module defines all possible errors that can occur during parsing
# of Protocol Buffer definition files (.proto), organized by category.

#               .'\   /`.
#             .'.-.`-'.-.`.
#        ..._:   .-. .-.   :_...
#      .'    '-.(o ) (o ).-'    `.
#     :  _    _ _`~(_)~`_ _    _  :
#    :  /:   ' .-=_   _=-. `   ;\  :
#    :   :|-.._  '     `  _..-|:   :
#     :   `:| |`:-:-.-:-:'| |:'   :
#      `.   `.| | | | | | |.'   .'
#        `.   `-:_| | |_:-'   .'
#          `-._   ````    _.-'
#              ``-------''
#
# Created by ab, 24.11.2025

from enum import Enum, auto

class ProtoError(Exception):
    """Custom exception for protobuf parsing errors."""
    def __init__(self, error_code: 'ParsingError', details: str = ""):
        self.error_code = error_code
        self.details = details
        message = f"Parsing failed with {error_code.name}"
        if details:
            message += f": {details}"
        super().__init__(message)
    
class ParsingError(Enum):
    """
    Comprehensive set of errors that can occur during Protocol Buffer parsing.
    Errors are grouped by category for better organization and documentation.
    """

    # === Syntax and Structure Errors === #

    # Invalid proto syntax definition (e.g., missing 'syntax' statement)
    InvalidSyntaxDef = auto()
    # Reached end of file unexpectedly while parsing
    UnexpectedEOF = auto()
    # Expected whitespace but found none
    SpaceRequired = auto()
    # Invalid or unsupported syntax version specified
    InvalidSyntaxVersion = auto()
    # Unexpected token encountered during parsing
    UnexpectedToken = auto()
    # Package has already been defined in this file
    PackageAlreadyDefined = auto()
    # Edition has already been defined in this file
    EditionAlreadyDefined = auto()

    # === String Parsing Errors === #

    # Invalid string literal format
    InvalidStringLiteral = auto()
    # Invalid Unicode escape sequence in string
    InvalidUnicodeEscape = auto()
    # Invalid escape sequence in string
    InvalidEscape = auto()

    # === Syntax Element Errors === #

    # Missing expected semicolon
    SemicolonExpected = auto()
    # Missing expected assignment operator
    AssignmentExpected = auto()
    # Missing expected bracket
    BracketExpected = auto()

    # === Identifier and Name Errors === #

    # Identifier must start with a letter
    IdentifierShouldStartWithLetter = auto()
    # Invalid option name format
    InvalidOptionName = auto()
    # Invalid field name format
    InvalidFieldName = auto()

    # === Value and Type Errors === #

    # Option declaration missing required value
    OptionValueRequired = auto()
    # Invalid integer literal format
    InvalidIntegerLiteral = auto()
    # Invalid boolean literal format
    InvalidBooleanLiteral = auto()
    # Invalid constant value
    InvalidConst = auto()
    # Invalid floating point number format
    InvalidFloat = auto()
    # Invalid field value
    InvalidFieldValue = auto()
    # Invalid map key type specified
    InvalidMapKeyType = auto()
    # Invalid map value type specified
    InvalidMapValueType = auto()

    # === Definition Errors === #

    # Invalid enum definition
    InvalidEnumDef = auto()
    # Invalid oneof element
    InvalidOneOfElement = auto()
    # Invalid extensions range specification
    InvalidExtensionsRange = auto()

    # === Reference and Resolution Errors === #

    # Referenced extend source type not found
    ExtendSourceNotFound = auto()
    # Referenced type not found
    TypeNotFound = auto()

    # === System and Runtime Errors === #

    # Numeric overflow occurred during parsing
    Overflow = auto()
    # Invalid character encountered
    InvalidCharacter = auto()
    # Memory allocation failed
    OutOfMemory = auto()

    # === Feature Support === #

    # Attempted to use an unsupported protocol buffer feature
    FeatureNotSupported = auto()