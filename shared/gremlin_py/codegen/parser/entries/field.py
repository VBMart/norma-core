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

from dataclasses import dataclass, field
from typing import Optional, List

from .buffer import ParserBuffer
from .errors import ProtoError as Error
from . import lexems as lex
from .option import Option
from .scoped_name import ScopedName
from .field_type import FieldType, SCALAR_TYPES


@dataclass
class OneOfField:
    """Represents a field within a oneof group"""
    start: int
    end: int
    f_type: FieldType
    f_name: str
    index: int
    options: Optional[List[Option]] = field(default_factory=list)

    @staticmethod
    def parse(scope: ScopedName, buf: ParserBuffer) -> "OneOfField":
        """
        Parses a single field within a oneof group
        Format: type name = number [options];
        """
        buf.skip_spaces()
        start = buf.offset

        f_type = FieldType.parse(scope, buf)
        f_name = lex.ident(buf)
        buf.assignment()
        f_number = lex.int_lit(buf)
        f_opts = Option.parse_list(buf)
        buf.semicolon()

        return OneOfField(
            start=start,
            end=buf.offset,
            f_type=f_type,
            f_name=f_name,
            index=int(f_number),
            options=f_opts,
        )

    def clone(self) -> "OneOfField":
        """Creates a deep copy of the OneOfField"""
        return OneOfField(
            start=self.start,
            end=self.end,
            f_type=self.f_type.clone(),
            f_name=self.f_name,
            index=self.index,
            options=[o.clone() for o in self.options] if self.options else None,
        )

@dataclass
class MessageOneOfField:
    """Represents a oneof group in a message"""
    start: int
    end: int
    name: str
    fields: List[OneOfField] = field(default_factory=list)
    options: List[Option] = field(default_factory=list)

    @staticmethod
    def parse(scope: ScopedName, buf: ParserBuffer) -> Optional["MessageOneOfField"]:
        """
        Parses a complete oneof declaration
        Format: oneof name { field1; field2; ... }
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_with_space_and_shift("oneof"):
            return None
        buf.skip_spaces()
        name = lex.ident(buf)
        buf.open_bracket()

        fields = []
        options = []

        while True:
            option = Option.parse(buf)
            if option:
                options.append(option)
            else:
                fields.append(OneOfField.parse(scope, buf))
            
            buf.skip_spaces()
            c = buf.char()
            if c == '}':
                buf.offset += 1
                break

        return MessageOneOfField(
            start=start,
            end=buf.offset,
            name=name,
            fields=fields,
            options=options,
        )
    
    def clone(self) -> "MessageOneOfField":
        """Creates a deep copy of the MessageOneOfField"""
        return MessageOneOfField(
            start=self.start,
            end=self.end,
            name=self.name,
            fields=[f.clone() for f in self.fields],
            options=[o.clone() for o in self.options],
        )


@dataclass
class MessageMapField:
    """Represents a map field in a message"""
    start: int
    end: int
    key_type: str
    value_type: FieldType
    f_name: str
    index: int
    options: Optional[List[Option]] = field(default_factory=list)

    @staticmethod
    def parse(scope: ScopedName, buf: ParserBuffer) -> Optional["MessageMapField"]:
        """
        Parses a map field declaration
        Format: map<key_type, value_type> name = number [options];
        """
        buf.skip_spaces()
        start = buf.offset

        if not buf.check_str_and_shift("map"):
            return None
        buf.skip_spaces()

        # Parse map type definition
        if buf.char() != '<':
            return None
        buf.offset += 1

        key_type = _map_key_type(buf)
        if key_type is None:
            raise Error("Invalid map key type")

        buf.skip_spaces()
        if buf.char() != ',':
            raise Error("Invalid map key type")
        buf.offset += 1

        value_type = FieldType.parse(scope, buf)
        if not value_type.src:
            raise Error("Invalid map value type")

        buf.skip_spaces()
        if buf.char() != '>':
            raise Error("Invalid map value type")
        buf.offset += 1

        # Parse field definition
        buf.skip_spaces()
        f_name = lex.ident(buf)
        buf.assignment()
        f_number = lex.int_lit(buf)
        options = Option.parse_list(buf)
        buf.semicolon()

        return MessageMapField(
            start=start,
            end=buf.offset,
            key_type=key_type,
            value_type=value_type,
            f_name=f_name,
            index=int(f_number),
            options=options,
        )

    def clone(self) -> "MessageMapField":
        """Creates a deep copy of the MessageMapField"""
        return MessageMapField(
            start=self.start,
            end=self.end,
            key_type=self.key_type,
            value_type=self.value_type.clone(),
            f_name=self.f_name,
            index=self.index,
            options=[o.clone() for o in self.options] if self.options else None,
        )


@dataclass
class NormalField:
    """Represents a normal field in a message"""
    start: int
    end: int
    repeated: bool
    optional: bool
    required: bool
    f_type: FieldType
    f_name: str
    index: int
    options: Optional[List[Option]] = field(default_factory=list)

    @staticmethod
    def parse(scope: ScopedName, buf: ParserBuffer) -> "NormalField":
        """
        Parses a normal field declaration
        Format: [repeated|optional|required] type name = number [options];
        """
        buf.skip_spaces()
        start = buf.offset

        # Parse field modifiers
        optional = buf.check_str_with_space_and_shift("optional")
        if optional:
            buf.skip_spaces()
        
        repeated = buf.check_str_with_space_and_shift("repeated")
        if repeated:
            buf.skip_spaces()

        required = buf.check_str_with_space_and_shift("required")
        if required:
            buf.skip_spaces()

        # Parse field definition
        f_type = FieldType.parse(scope, buf)
        f_name = lex.ident(buf)
        buf.assignment()
        f_number = lex.int_lit(buf)
        f_opts = Option.parse_list(buf)
        buf.semicolon()

        return NormalField(
            start=start,
            end=buf.offset,
            repeated=repeated,
            optional=optional,
            required=required,
            f_type=f_type,
            f_name=f_name,
            index=int(f_number),
            options=f_opts,
        )

    def clone(self) -> "NormalField":
        """Creates a deep copy of the NormalField"""
        return NormalField(
            start=self.start,
            end=self.end,
            repeated=self.repeated,
            optional=self.optional,
            required=self.required,
            f_type=self.f_type.clone(),
            f_name=self.f_name,
            index=self.index,
            options=[o.clone() for o in self.options] if self.options else None,
        )


def _map_key_type(buf: ParserBuffer) -> Optional[str]:
    """Parses a map key type (scalar types, string, or bytes)"""
    buf.skip_spaces()

    # Check scalar types
    for key_type in SCALAR_TYPES:
        if buf.check_str_and_shift(key_type):
            return key_type

    # Check string/bytes types
    if buf.check_str_and_shift("string"):
        return "string"
    if buf.check_str_and_shift("bytes"):
        return "bytes"

    return None
