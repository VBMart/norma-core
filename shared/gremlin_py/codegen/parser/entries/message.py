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
from . import lexems as lex
from .option import Option
from .reserved import Reserved
from .extension import Extensions
from .extend import Extend
from . import field as fields
from .enum import Enum
from .group import Group
from .scoped_name import ScopedName


@dataclass
class Message:
    """
    Represents a Protocol Buffer message definition.
    Messages can contain fields, nested messages/enums, options,
    and other elements that define the message structure.
    """
    start: int
    end: int
    name: ScopedName
    options: List[Option] = field(default_factory=list)
    oneofs: List[fields.MessageOneOfField] = field(default_factory=list)
    maps: List[fields.MessageMapField] = field(default_factory=list)
    fields: List[fields.NormalField] = field(default_factory=list)
    reserved: List[Reserved] = field(default_factory=list)
    extensions: List[Extensions] = field(default_factory=list)
    extends: List[Extend] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)
    enums: List[Enum] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    parent: Optional[Message] = None
    
    @staticmethod
    def parse(buf: ParserBuffer, parent: Optional[ScopedName]) -> Optional[Message]:
        """
        Parses a message definition including all its contents.
        Handles nested messages, enums, fields, and all other valid
        message elements.

        Args:
            buf: Parser buffer containing the message.
            parent: Parent scope if this is a nested message.

        Returns:
            The parsed message or None if the input doesn't start with a message.

        Raises:
            ProtoError: On invalid syntax.
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_with_space_and_shift("message"):
            return None

        name = lex.ident(buf)
        buf.open_bracket()

        scoped = parent.child(name) if parent else ScopedName(name)

        options = []
        oneofs = []
        maps = []
        mfields = []
        enums = []
        messages = []
        reserved = []
        extensions = []
        extends = []
        groups = []

        while True:
            buf.skip_spaces()
            c = buf.char()
            if c == '}':
                buf.offset += 1
                break
            elif c == ';':
                buf.offset += 1
                continue

            opt = Option.parse(buf)
            if opt:
                options.append(opt)
                continue

            oneof = fields.MessageOneOfField.parse(scoped, buf)
            if oneof:
                oneofs.append(oneof)
                continue
            
            map_field = fields.MessageMapField.parse(scoped, buf)
            if map_field:
                maps.append(map_field)
                continue

            res = Reserved.parse(buf)
            if res:
                reserved.append(res)
                continue
            
            ext = Extensions.parse(buf)
            if ext:
                extensions.append(ext)
                continue

            extend = Extend.parse(buf)
            if extend:
                extends.append(extend)
                continue

            group = Group.parse(buf)
            if group:
                groups.append(group)
                continue

            enum = Enum.parse(buf, scoped)
            if enum:
                enums.append(enum)
                continue

            msg = Message.parse(buf, scoped)
            if msg:
                messages.append(msg)
                continue

            mfields.append(fields.NormalField.parse(scoped, buf))

        return Message(
            start=start,
            end=buf.offset,
            name=scoped,
            options=options,
            oneofs=oneofs,
            maps=maps,
            fields=mfields,
            reserved=reserved,
            extensions=extensions,
            extends=extends,
            groups=groups,
            enums=enums,
            messages=messages,
        )

    def has_fields(self) -> bool:
        """Returns whether the message has any field definitions"""
        return len(self.fields) > 0 or len(self.oneofs) > 0 or len(self.maps) > 0