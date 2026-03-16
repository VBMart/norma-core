# //! Protocol buffer wire format encoder/decoder implementation
# //! Provides functionality for reading and writing protocol buffer wire format messages
# //!
# //! Main components:
# //! - Writer: Handles encoding messages to wire format
# //! - Reader: Handles decoding wire format messages
# //! - ProtoWireNumber: Field numbers for proto fields
# //! - ProtoWireType: Wire types for proto fields

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

from . import sizes
from .reader import Reader
from .writer import (Writer, StreamingWriter)
from .types import (
    ProtoWireNumber,
    ProtoWireType,
    GremlinError,
    InvalidDataError,
    InvalidTagError,
    InvalidVarIntError,
)

__all__ = [
    "Reader",
    "Writer",
    "ProtoWireNumber",
    "ProtoWireType",
    "sizes",
    "GremlinError",
    "InvalidDataError",
    "InvalidTagError",
    "InvalidVarIntError",
]