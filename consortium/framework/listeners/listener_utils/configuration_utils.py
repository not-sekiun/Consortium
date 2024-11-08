"""
This module contains utility functions that help in configuring listeners.
"""

import ipaddress
import platform
import socket
import subprocess


def get_local_host_address() -> str:
    """
    This function attempts to get the local host IP address of the system. If it fails
    to do so, it returns the loopback address.

    Returns:
        str: The local host IP address of the system.
    """
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_socket.settimeout(0)
    try:
        test_socket.connect(("10.254.254.254", 1))
        local_host_address = test_socket.getsockname()[0]
    except Exception:
        local_host_address = "127.0.0.1"
    finally:
        test_socket.close()
    return local_host_address


def check_socket_address_availability(
    local_host_address: str,
    local_port: int,
) -> bool:
    """
    This function checks if a given socket address is available for use to be bound on.

    Args:
        local_host_address (str): The local host address to check.
        local_port (int): The local port to check.

    Returns:
        bool: `True` if the socket address is available, `False` otherwise.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
            test_socket.bind((local_host_address, local_port))
    except OSError:
        return False
    return True


def get_available_port(
    start_port: int = 49152,
    end_port: int = 65535,
    local_host_address: str = "127.0.0.1",
) -> int | None:
    """
    Find an available port within a specified range.

    Args:
        start_port (int, optional): Starting port of the range. Defaults to 49152 (dynamic/private port range start).
        end_port (int, optional): Ending port of the range. Defaults to 65535.
        local_host_address (str, optional): Local host address to check port
            availability. Defaults to localhost.

    Returns:
        int | None: An available port number, or None if no port is available.
    """
    for port in range(start_port, end_port + 1):
        if check_socket_address_availability(local_host_address, port):
            return port
    return None


def validate_ip_address(ip_address: str) -> bool:
    """
    Validate whether a given string is a valid IP address.

    Args:
        ip_address (str): IP address to validate.

    Returns:
        bool: True if the IP address is valid, False otherwise.
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except ValueError:
        return False


def get_network_interfaces() -> list[tuple[str, str]]:
    """
    Retrieve a list of network interfaces with their IP addresses.

    Returns:
        list[tuple[str, str]]: A list of tuples containing the interface name and IP address.
    """
    system = platform.system()
    interfaces = []

    try:
        if system == "Windows":
            result = subprocess.run(["ipconfig"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "IPv4 Address" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ip_address = parts[1].strip()
                        interfaces.append(("Windows Interface", ip_address))
        elif system in ["Linux", "Darwin"]:
            result = subprocess.run(["ip", "addr"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "inet " in line and not "127.0.0.1" in line:
                    ip_address = line.split()[1].split("/")[0]
                    interface = line.split()[6] if len(line.split()) > 6 else "Unknown"
                    interfaces.append((interface, ip_address))
    except Exception:
        # Fallback to socket method if subprocess fails.
        try:
            hostname = socket.gethostname()
            addresses = socket.getaddrinfo(hostname, None)
            for addr in addresses:
                if addr[0] == socket.AF_INET:
                    interfaces.append(("Socket Interface", addr[4][0]))
        except Exception:
            pass

    return interfaces


def check_valid_port_number(port: int) -> bool:
    """
    Check if a given port number is valid.

    Args:
        port (int): Port number to check.

    Returns:
        bool: True if the port number is valid, False otherwise.
    """
    return 0 < port < 65536
