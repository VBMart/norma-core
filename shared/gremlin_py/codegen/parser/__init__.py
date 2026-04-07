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
# Created by ab, 25.11.2025

"""
This module re-exports the main components of the parser, making them
available at the package level.
"""

from .parser import parse, ParseResult
from .entries.buffer import ParserBuffer
from .entries.file import ProtoFile
from .entries.imports import Import, ImportType
from .entries.enum import Enum
from .entries.message import Message
from .entries import field as fields
from .entries.field_type import FieldType
from .entries.scoped_name import ScopedName
from .entries.option import Option

__all__ = [
    "parse",
    "ParseResult",
    "ParserBuffer",
    "ProtoFile",
    "Import",
    "ImportType",
    "Enum",
    "Message",
    "fields",
    "FieldType",
    "ScopedName",
    "Option",
]