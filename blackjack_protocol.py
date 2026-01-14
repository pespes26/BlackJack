"""
Blackjack Protocol Module
Defines all protocol constants and helper functions for packet encoding/decoding.
This module is shared between the client and server.
"""

import struct
import socket

# ============================================================================
# PROTOCOL CONSTANTS
# ============================================================================

# Magic cookie for all messages (0xabcddcba)
MAGIC_COOKIE = 0xabcddcba

# Message types
MSG_TYPE_OFFER = 0x2      # Server to client (UDP)
MSG_TYPE_REQUEST = 0x3    # Client to server (TCP)
MSG_TYPE_PAYLOAD = 0x4    # Bidirectional (TCP)

# Round results (server to client in payload)
RESULT_NOT_OVER = 0x0
RESULT_TIE = 0x1
RESULT_LOSS = 0x2
RESULT_WIN = 0x3

# Player decisions (client to server in payload)
DECISION_HIT = "Hittt"
DECISION_STAND = "Stand"

# Field sizes
NAME_SIZE = 32            # Server/client name field size

# UDP broadcast port for offer messages
OFFER_PORT = 13122

# Card suits (0-3 for HDCS)
SUIT_HEART = 0
SUIT_DIAMOND = 1
SUIT_CLUB = 2
SUIT_SPADE = 3

SUIT_NAMES = {
    SUIT_HEART: "♥",
    SUIT_DIAMOND: "♦",
    SUIT_CLUB: "♣",
    SUIT_SPADE: "♠"
}

SUIT_COLORS = {
    SUIT_HEART: "red",
    SUIT_DIAMOND: "red",
    SUIT_CLUB: "black",
    SUIT_SPADE: "black"
}

# Card ranks (1-13)
RANK_NAMES = {
    1: "A",
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
    11: "J", 12: "Q", 13: "K"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_card_value(rank):
    """
    Get the point value of a card based on its rank.
    
    Args:
        rank (int): Card rank (1-13)
        
    Returns:
        int: Point value (Ace=11, Face=10, Number=face value)
    """
    if rank == 1:  # Ace
        return 11
    elif rank >= 11:  # J, Q, K
        return 10
    else:  # 2-10
        return rank


def format_card(rank, suit):
    """
    Format a card for display.
    
    Args:
        rank (int): Card rank (1-13)
        suit (int): Card suit (0-3)
        
    Returns:
        str: Formatted card string (e.g., "A♥", "K♠")
    """
    rank_name = RANK_NAMES.get(rank, "?")
    suit_symbol = SUIT_NAMES.get(suit, "?")
    return f"{rank_name}{suit_symbol}"


def pad_name(name):
    """
    Pad or truncate a name to NAME_SIZE bytes.
    
    Args:
        name (str): Name to pad/truncate
        
    Returns:
        bytes: NAME_SIZE bytes
    """
    name_bytes = name.encode('utf-8')
    if len(name_bytes) > NAME_SIZE:
        return name_bytes[:NAME_SIZE]
    else:
        return name_bytes.ljust(NAME_SIZE, b'\x00')


def unpad_name(name_bytes):
    """
    Remove padding from a NAME_SIZE name field.
    
    Args:
        name_bytes (bytes): Padded name bytes
        
    Returns:
        str: Unpadded name string
    """
    # Remove null bytes and decode
    return name_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')


# ============================================================================
# OFFER MESSAGE (UDP: Server -> Client)
# Format: Magic(4) + Type(1) + Port(2) + Name(32) = 39 bytes
# ============================================================================

def create_offer_message(tcp_port, server_name):
    """
    Create an offer message for UDP broadcast.
    
    Args:
        tcp_port (int): TCP port number the server is listening on
        server_name (str): Server name (will be padded/truncated to 32 bytes)
        
    Returns:
        bytes: Encoded offer message (39 bytes)
    """
    return struct.pack('!IBH', MAGIC_COOKIE, MSG_TYPE_OFFER, tcp_port) + pad_name(server_name)


def parse_offer_message(data):
    """
    Parse an offer message from UDP.
    
    Args:
        data (bytes): Raw message data
        
    Returns:
        tuple: (tcp_port, server_name) or None if invalid
    """
    if len(data) < 39:
        return None
    
    try:
        magic, msg_type, tcp_port = struct.unpack('!IBH', data[:7])
        
        if magic != MAGIC_COOKIE or msg_type != MSG_TYPE_OFFER:
            return None
        
        server_name = unpad_name(data[7:39])
        return (tcp_port, server_name)
    except:
        return None


# ============================================================================
# REQUEST MESSAGE (TCP: Client -> Server)
# Format: Magic(4) + Type(1) + Rounds(1) + Name(32) = 38 bytes
# ============================================================================

def create_request_message(num_rounds, client_name):
    """
    Create a request message for TCP connection.
    
    Args:
        num_rounds (int): Number of rounds to play
        client_name (str): Client team name (will be padded/truncated to 32 bytes)
        
    Returns:
        bytes: Encoded request message (38 bytes)
    """
    return struct.pack('!IBB', MAGIC_COOKIE, MSG_TYPE_REQUEST, num_rounds) + pad_name(client_name)


def parse_request_message(data):
    """
    Parse a request message from TCP.
    
    Args:
        data (bytes): Raw message data
        
    Returns:
        tuple: (num_rounds, client_name) or None if invalid
    """
    if len(data) < 38:
        return None
    
    try:
        magic, msg_type, num_rounds = struct.unpack('!IBB', data[:6])
        
        if magic != MAGIC_COOKIE or msg_type != MSG_TYPE_REQUEST:
            return None
        
        client_name = unpad_name(data[6:38])
        return (num_rounds, client_name)
    except:
        return None


# ============================================================================
# PAYLOAD MESSAGE (TCP: Bidirectional)
# Client: Magic(4) + Type(1) + Decision(5) = 10 bytes
# Server: Magic(4) + Type(1) + Result(1) + Rank(2) + Suit(1) = 9 bytes
# ============================================================================

def create_client_payload(decision):
    """
    Create a client payload message (player decision).
    
    Args:
        decision (str): "Hittt" or "Stand"
        
    Returns:
        bytes: Encoded client payload message (10 bytes)
    """
    decision_bytes = decision.encode('utf-8')[:5].ljust(5, b'\x00')
    return struct.pack('!IB', MAGIC_COOKIE, MSG_TYPE_PAYLOAD) + decision_bytes


def create_server_payload(result, rank, suit):
    """
    Create a server payload message (card and result).
    
    Args:
        result (int): Round result (0x0-0x3)
        rank (int): Card rank (1-13), encoded as 2 bytes
        suit (int): Card suit (0-3)
        
    Returns:
        bytes: Encoded server payload message (9 bytes)
    """
    return struct.pack('!IBBHB', MAGIC_COOKIE, MSG_TYPE_PAYLOAD, result, rank, suit)


def parse_client_payload(data):
    """
    Parse a client payload message.
    
    Args:
        data (bytes): Raw message data
        
    Returns:
        str: Decision ("Hittt" or "Stand") or None if invalid
    """
    if len(data) < 10:
        return None
    
    try:
        magic, msg_type = struct.unpack('!IB', data[:5])
        
        if magic != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return None
        
        decision = data[5:10].rstrip(b'\x00').decode('utf-8', errors='ignore')
        return decision
    except:
        return None


def parse_server_payload(data):
    """
    Parse a server payload message.
    
    Args:
        data (bytes): Raw message data
        
    Returns:
        tuple: (result, rank, suit) or None if invalid
    """
    if len(data) < 9:
        return None
    
    try:
        magic, msg_type, result, rank, suit = struct.unpack('!IBBHB', data[:9])
        
        if magic != MAGIC_COOKIE or msg_type != MSG_TYPE_PAYLOAD:
            return None
        
        return (result, rank, suit)
    except:
        return None


# ============================================================================
# NETWORK UTILITIES
# ============================================================================

def get_wifi_ip():
    """
    Get the IP address of the Wireless LAN adapter Wi-Fi interface.
    
    This function detects the Wi-Fi adapter by searching for interfaces
    with common Wi-Fi adapter names on Windows.
    
    Returns:
        str: Wi-Fi adapter IP address or None if not found
    """
    import subprocess
    import re
    
    try:
        # Run ipconfig to get all network adapters on Windows
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        output = result.stdout
        
        # Look for Wireless LAN adapter followed by IPv4 address
        # Handle multiline format where adapter name might wrap
        lines = output.split('\n')
        in_wifi_section = False
        
        for i, line in enumerate(lines):
            # Check if this line indicates a Wireless LAN adapter
            if 'Wireless LAN adapter' in line or 'Wi-Fi' in line:
                in_wifi_section = True
                continue
            
            # If we're in the WiFi section, look for IPv4 address
            if in_wifi_section:
                # End section if we hit another adapter
                if 'adapter' in line and line.strip().endswith(':'):
                    in_wifi_section = False
                    continue
                
                # Look for IPv4 address
                ipv4_match = re.search(r'IPv4 Address[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)', line)
                if ipv4_match:
                    ip = ipv4_match.group(1)
                    # Ignore APIPA addresses (169.254.x.x)
                    if not ip.startswith('169.254'):
                        return ip
        
        return None
    except Exception as e:
        print(f"Error detecting Wi-Fi adapter: {e}")
        return None


def get_local_ip():
    """
    Get the local IP address of this machine, preferring Wi-Fi adapter.
    
    Returns:
        str: Local IP address (Wi-Fi preferred, fallback to any available)
    """
    # First, try to get Wi-Fi adapter IP
    wifi_ip = get_wifi_ip()
    if wifi_ip:
        print(f"Using Wi-Fi adapter IP: {wifi_ip}")
        return wifi_ip
    
    # Fallback to the original method if Wi-Fi not found
    try:
        # Connect to an external IP to determine local IP
        # We don't actually send data, just use it to find our interface
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"Warning: Wi-Fi adapter not found, using default interface: {ip}")
        return ip
    except:
        print("Warning: Could not detect network interface, using localhost")
        return "127.0.0.1"


def get_broadcast_address():
    """
    Get the broadcast address for the local network.
    
    Returns:
        str: Broadcast address (e.g., "255.255.255.255")
    """
    # Use limited broadcast address
    return "255.255.255.255"
