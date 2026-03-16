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

from .buffer import ParserBuffer
from .errors import ProtoError, ParsingError

class Service:
    """
    Represents a service definition in a protobuf file.
    A service definition contains RPC method definitions.
    Format:
    ```protobuf
    service Greeter {
        rpc SayHello (HelloRequest) returns (HelloResponse);
        rpc SayGoodbye (GoodbyeRequest) returns (GoodbyeResponse);
    }
    ```
    """

    @staticmethod
    def parse(buf: ParserBuffer) -> 'Service | None':
        """
        Attempts to parse a service definition from the given buffer.
        Returns None if the buffer doesn't start with a service definition.
        Returns error for malformed service definitions.

        The parser currently skips the entire service body, counting braces
        to ensure proper nesting. Future versions should parse the RPC methods.

        :param buf: The buffer to parse.
        :return: A Service instance or None.
        :raises ProtoError: For malformed service definitions.
        """
        buf.skip_spaces()

        if not buf.check_str_with_space_and_shift("service"):
            return None

        # Count opening and closing braces to handle nested blocks
        brace_count = 0
        while True:
            try:
                c = buf.should_shift_next()
                if c == '{':
                    brace_count += 1
                elif c == '}':
                    if brace_count == 0:
                        raise ProtoError(ParsingError.UnexpectedEOF)
                    brace_count -= 1
                    if brace_count == 0:
                        break
            except ProtoError as e:
                if e.error_code == ParsingError.UnexpectedEOF:
                    raise ProtoError(ParsingError.UnexpectedEOF, "Buffer ends before service definition is complete")
                else:
                    raise

        return Service()