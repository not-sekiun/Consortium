import socket


def get_local_ip() -> str:
    """Return the local IP address selected for an outbound UDP connection.

    Returns:
        The selected local IP address, or ``127.0.0.1`` if it cannot be determined.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip
