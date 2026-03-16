class NormfsError(Exception):
    """Base exception for normfs client."""
    pass

class ErrNotConnected(NormfsError):
    """Client not connected or setup not complete."""
    pass

class ErrBufferFull(NormfsError):
    """Client request buffer is full."""
    pass

class ErrRequestTimeout(NormfsError):
    """Request timed out waiting for server response."""
    pass

class ErrConnectionClosed(NormfsError):
    """Connection closed while waiting for response."""
    pass

class ErrInvalidResponse(NormfsError):
    """Invalid or unexpected response from server."""
    pass

class ErrServerSide(NormfsError):
    """Server returned an error."""
    pass

class ErrQueueNotFound(NormfsError):
    """Queue not found on server."""
    pass

class ErrReadStreamClosed(NormfsError):
    """Read stream closed by server or connection error."""
    pass

class ErrEntryNotFound(NormfsError):
    """Entry not found on server."""
    pass
