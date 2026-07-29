import ipaddress
import platform
import socket
import subprocess

import aiohttp


def get_local_ip(fallback: str = "127.0.0.1") -> str:
    """Return the local address selected for an outbound connection.

    Args:
        fallback: Address to return when the local address cannot be determined.

    Returns:
        The selected local IP address or the fallback address.
    """
    socket_handle = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        socket_handle.connect(("10.255.255.255", 1))
        return socket_handle.getsockname()[0]
    except OSError:
        return fallback
    finally:
        socket_handle.close()


def is_valid_ip(value: str) -> bool:
    """Check whether a value is a valid IPv4 or IPv6 address.

    Args:
        value: Address string to validate.

    Returns:
        True when the value is a valid IP address, otherwise False.
    """
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def is_valid_port(port: int) -> bool:
    """Check whether a port number can be used for a network socket.

    Args:
        port: Port number to validate.

    Returns:
        True when the port is in the range 1 through 65535, otherwise False.
    """
    return 0 < port < 65536


def is_bindable(address: str, port: int) -> bool:
    """Check whether a TCP socket can currently bind to an address and port.

    Args:
        address: Local address to bind.
        port: Port to bind.

    Returns:
        True when the socket can be bound, otherwise False.
    """
    if not is_valid_port(port):
        return False

    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    try:
        with socket.socket(family, socket.SOCK_STREAM) as socket_handle:
            socket_handle.bind((address, port))
    except OSError:
        return False
    return True


def find_available_port(
    address: str = "127.0.0.1",
    start: int = 49152,
    end: int = 65535,
) -> int | None:
    """Find the first available port in an inclusive range.

    Args:
        address: Local address against which to test each port.
        start: First port in the search range.
        end: Last port in the search range.

    Returns:
        The first bindable port, or None when no port is available.

    Raises:
        ValueError: If the range is reversed or either boundary is invalid.
    """
    if start > end:
        raise ValueError("start must not be greater than end")
    if not is_valid_port(start) or not is_valid_port(end):
        raise ValueError("start and end must be valid port numbers")

    for port in range(start, end + 1):
        if is_bindable(address, port):
            return port
    return None


def get_network_interfaces() -> list[tuple[str, str]]:
    """Return discovered network-interface names and IPv4 addresses.

    Returns:
        Interface-name and IP-address pairs discovered from the operating system.
    """
    system = platform.system()
    interfaces: list[tuple[str, str]] = []

    try:
        if system == "Windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "IPv4 Address" in line:
                    _, _, ip_address = line.partition(":")
                    if ip_address:
                        interfaces.append(("Windows Interface", ip_address.strip()))
        elif system in ("Linux", "Darwin"):
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) > 1 and parts[0] == "inet" and parts[1] != "127.0.0.1":
                    interface = parts[6] if len(parts) > 6 else "Unknown"
                    interfaces.append((interface, parts[1].split("/", 1)[0]))
    except OSError:
        try:
            hostname = socket.gethostname()
            for address in socket.getaddrinfo(hostname, None, socket.AF_INET):
                interfaces.append(("Socket Interface", address[4][0]))
        except OSError:
            pass

    return interfaces


async def get_public_ip(*, timeout_seconds: float = 5.0) -> str | None:
    """Resolve the public IP address reported by the external IP service.

    Args:
        timeout_seconds: Maximum time to wait for the external request.

    Returns:
        The reported public IP address, or None when it cannot be resolved.
    """
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://api.ipify.org") as response:
                response.raise_for_status()
                return await response.text()
    except (aiohttp.ClientError, TimeoutError):
        return None
