"""
Protocol Buffer file parser module.
Handles parsing complete .proto files, including all definitions like
packages, imports, messages, enums, services, and options.
"""

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

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .buffer import ParserBuffer
from .errors import ProtoError, ParsingError
from .syntax import Syntax
from .enum import Enum
from .message import Message
from .imports import Import
from .package import Package
from .option import Option
from .service import Service
from .edition import Edition
from .extend import Extend
from .scoped_name import ScopedName

@dataclass
class ProtoFile:
    """
    Represents a complete Protocol Buffer definition file.
    Contains all declarations and definitions found in a .proto file.
    """
    syntax: Optional[Syntax] = None
    package: Optional[Package] = None
    edition: Optional[Edition] = None
    path: Optional[str] = None
    options: List[Option] = field(default_factory=list)
    imports: List[Import] = field(default_factory=list)
    enums: List[Enum] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    services: List[Service] = field(default_factory=list)
    extends: List[Extend] = field(default_factory=list)

    @staticmethod
    def parse(buf: ParserBuffer) -> ProtoFile:
        """
        Parses a complete Protocol Buffer file.
        Handles all top-level declarations including syntax, package, imports,
        messages, enums, services, and options.

        The parser processes declarations in any order and validates that
        certain declarations (syntax, package, edition) appear only once.

        # Errors
        - PackageAlreadyDefined if multiple package statements
        - EditionAlreadyDefined if multiple edition statements
        - UnexpectedToken if unknown content encountered
        """
        buf.skip_spaces()

        syntax: Optional[Syntax] = None
        package: Optional[Package] = None
        edition: Optional[Edition] = None
        imports: List[Import] = []
        enums: List[Enum] = []
        messages: List[Message] = []
        options: List[Option] = []
        services: List[Service] = []
        extends: List[Extend] = []

        s = Syntax.parse(buf)
        if s:
            syntax = s

        scope = ScopedName(".")

        while True:
            buf.skip_spaces()
            found = False

            p = Package.parse(buf)
            if p:
                if package is not None:
                    raise ProtoError(ParsingError.PackageAlreadyDefined)
                package = p
                scope = p.name
                found = True
                continue

            e = Edition.parse(buf)
            if e:
                if edition is not None:
                    raise ProtoError(ParsingError.EditionAlreadyDefined)
                edition = e
                found = True
                continue

            i = Import.parse(buf)
            if i:
                imports.append(i)
                found = True
                continue

            m = Message.parse(buf, scope)
            if m:
                messages.append(m)
                found = True
                continue

            en = Enum.parse(buf, scope)
            if en:
                enums.append(en)
                found = True
                continue

            o = Option.parse(buf)
            if o:
                options.append(o)
                found = True
                continue

            s = Service.parse(buf)
            if s:
                services.append(s)
                found = True
                continue

            ex = Extend.parse(buf)
            if ex:
                extends.append(ex)
                found = True
                continue

            c = buf.char()
            if c == ';':
                buf.offset += 1
                found = True
            elif c is None:
                break

            if not found:
                raise ProtoError(ParsingError.UnexpectedToken)

        return ProtoFile(
            syntax=syntax,
            package=package,
            options=options,
            edition=edition,
            imports=imports,
            enums=enums,
            extends=extends,
            messages=messages,
            services=services,
        )