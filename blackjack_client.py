#!/usr/bin/env python3
"""
Blackjack Client
Listens for server offers via UDP and connects via TCP to play Blackjack.
"""

import socket
import sys
import time
from blackjack_protocol import *

# ============================================================================
# ANSI COLOR CODES FOR PRETTY OUTPUT
# ============================================================================

class Colors:
    """Gentle, elegant color palette for a beautiful UI"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Soft, gentle colors
    CORAL = '\033[38;5;210m'      # Soft coral for wins
    MINT = '\033[38;5;158m'        # Mint green for success
    LAVENDER = '\033[38;5;183m'    # Lavender for info
    PEACH = '\033[38;5;223m'       # Soft peach for warnings
    POWDER_BLUE = '\033[38;5;153m' # Powder blue for headers
    ROSE = '\033[38;5;217m'        # Soft rose for losses
    CREAM = '\033[38;5;230m'       # Cream for text
    SAGE = '\033[38;5;151m'        # Sage green for dealer
    
    # Card suit colors (gentle versions)
    RED_SOFT = '\033[38;5;210m'    # Soft red for hearts/diamonds
    BLACK_SOFT = '\033[38;5;243m'  # Soft black for spades/clubs

# ============================================================================
# CONFIGURATION
# ============================================================================

CLIENT_NAME = "🌀 Rasengan Gamblers 🌀"  # Spiral into victory!
UDP_TIMEOUT = 10.0  # Timeout for waiting for server offers
TCP_TIMEOUT = 30.0  # TCP connection timeout

# ============================================================================
# CLIENT GAME SESSION
# ============================================================================

class BlackjackClient:
    """Manages client-side Blackjack game session."""
    
    def __init__(self, server_ip, server_port, server_name, num_rounds):
        """
        Initialize client session.
        
        Args:
            server_ip (str): Server IP address
            server_port (int): Server TCP port
            server_name (str): Server name
            num_rounds (int): Number of rounds to play
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_name = server_name
        self.num_rounds = num_rounds
        self.tcp_socket = None
        
        self.player_hand = []
        self.dealer_hand = []
        self.wins = 0
        self.losses = 0
        self.ties = 0
    
    def connect(self):
        """
        Connect to the server via TCP.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"{Colors.LAVENDER}Connecting to {self.server_name} at {self.server_ip}:{self.server_port}...{Colors.RESET}")
            
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.settimeout(TCP_TIMEOUT)
            
            # Bind to Wi-Fi adapter before connecting
            wifi_ip = get_local_ip()
            self.tcp_socket.bind((wifi_ip, 0))
            
            self.tcp_socket.connect((self.server_ip, self.server_port))
            
            print(f"{Colors.MINT}✓ Connected successfully!{Colors.RESET}\n")
            
            # Send request message
            request_msg = create_request_message(self.num_rounds, CLIENT_NAME)
            self.tcp_socket.sendall(request_msg)
            
            return True
            
        except socket.timeout:
            print(f"{Colors.ROSE}✗ Connection timeout{Colors.RESET}")
            return False
        except Exception as e:
            print(f"{Colors.ROSE}✗ Connection error: {e}{Colors.RESET}")
            return False
    
    def send_decision(self, decision):
        """
        Send a decision to the server.
        
        Args:
            decision (str): "Hittt" or "Stand"
        """
        message = create_client_payload(decision)
        self.tcp_socket.sendall(message)
    
    def receive_card(self):
        """
        Receive a card from the server.
        
        Returns:
            tuple: (result, rank, suit) or None if error
        """
        try:
            data = self.tcp_socket.recv(9)
            if not data:
                return None
            return parse_server_payload(data)
        except socket.timeout:
            print(f"{Colors.ROSE}Timeout waiting for card{Colors.RESET}")
            return None
        except Exception as e:
            print(f"{Colors.ROSE}Error receiving card: {e}{Colors.RESET}")
            return None
    
    def calculate_hand_value(self, hand):
        """
        Calculate total value of a hand.
        
        Args:
            hand (list): List of (rank, suit) tuples
            
        Returns:
            int: Total value
        """
        total = sum(get_card_value(rank) for rank, suit in hand)
        
        # Count number of aces (rank = 1)
        num_aces = sum(1 for rank, suit in hand if rank == 1)
        
        # Adjust for aces: while total > 21 and we have aces counted as 11, convert them to 1
        while total > 21 and num_aces > 0:
            total -= 10  # Convert one ace from 11 to 1
            num_aces -= 1
        
        return total
    
    def draw_card_art(self, rank, suit):
        """
        Create ASCII art for a single card.
        
        Args:
            rank (int): Card rank (1-13)
            suit (int): Card suit (1-4)
            
        Returns:
            list: List of strings representing card lines
        """
        rank_str = RANK_NAMES.get(rank, "?")
        suit_symbol = SUIT_NAMES.get(suit, "?")
        
        # Choose color based on suit
        if SUIT_COLORS[suit] == "red":
            color = Colors.RED_SOFT
        else:
            color = Colors.BLACK_SOFT
        
        # Build card (7 lines tall, 11 chars wide)
        card_lines = [
            f"{Colors.POWDER_BLUE}┌─────────┐{Colors.RESET}",
            f"{Colors.POWDER_BLUE}│{Colors.RESET}{color}{rank_str:<2}{Colors.RESET}       {Colors.POWDER_BLUE}│{Colors.RESET}",
            f"{Colors.POWDER_BLUE}│{Colors.RESET}         {Colors.POWDER_BLUE}│{Colors.RESET}",
            f"{Colors.POWDER_BLUE}│{Colors.RESET}    {color}{suit_symbol}{Colors.RESET}    {Colors.POWDER_BLUE}│{Colors.RESET}",
            f"{Colors.POWDER_BLUE}│{Colors.RESET}         {Colors.POWDER_BLUE}│{Colors.RESET}",
            f"{Colors.POWDER_BLUE}│{Colors.RESET}       {color}{rank_str:>2}{Colors.RESET}{Colors.POWDER_BLUE}│{Colors.RESET}",
            f"{Colors.POWDER_BLUE}└─────────┘{Colors.RESET}",
        ]
        
        return card_lines
    
    def format_hand(self, hand):
        """
        Format hand as ASCII art cards displayed side by side.
        
        Args:
            hand (list): List of (rank, suit) tuples
            
        Returns:
            str: Multi-line string with cards side by side
        """
        if not hand:
            return ""
        
        # Get all card art
        all_cards = [self.draw_card_art(rank, suit) for rank, suit in hand]
        
        # Combine cards horizontally
        result_lines = []
        for line_idx in range(7):  # 7 lines per card
            line_parts = []
            for card_art in all_cards:
                line_parts.append(card_art[line_idx])
            result_lines.append(" ".join(line_parts))
        
        return "\n".join(result_lines)
    
    def get_user_decision(self):
        """
        Prompt user for hit or stand decision.
        
        Returns:
            str: "Hittt" or "Stand"
        """
        while True:
            try:
                choice = input(f"{Colors.PEACH}→ Do you want to [H]it or [S]tand? {Colors.RESET}").strip().upper()
                if choice in ['H', 'HIT']:
                    return DECISION_HIT
                elif choice in ['S', 'STAND']:
                    return DECISION_STAND
                else:
                    print(f"{Colors.DIM}  Invalid choice. Please enter H or S.{Colors.RESET}")
            except KeyboardInterrupt:
                print(f"\n{Colors.PEACH}Exiting...{Colors.RESET}")
                sys.exit(0)
            except:
                print(f"{Colors.DIM}  Invalid input. Please try again.{Colors.RESET}")
    
    def play_round(self, round_num):
        """
        Play a single round.
        
        Args:
            round_num (int): Round number
            
        Returns:
            bool: True if round completed successfully
        """
        print(f"\n{Colors.POWDER_BLUE}╭{'─'*58}╮{Colors.RESET}")
        round_text = f"Round {round_num}/{self.num_rounds}"
        padding = 58 - len(round_text) - 1
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET} {Colors.BOLD}{round_text}{Colors.RESET}{' '*padding}{Colors.POWDER_BLUE}│{Colors.RESET}")
        print(f"{Colors.POWDER_BLUE}╰{'─'*58}╯{Colors.RESET}\n")
        
        self.player_hand = []
        self.dealer_hand = []
        dealer_hidden_card = None
        
        # Receive initial cards (2 for player, 1 visible for dealer)
        print(f"{Colors.LAVENDER}Dealing cards...{Colors.RESET}")
        
        # Player's first card
        card_data = self.receive_card()
        if not card_data:
            return False
        result, rank, suit = card_data
        self.player_hand.append((rank, suit))
        print(f"{Colors.DIM}  ├─{Colors.RESET} You receive: {format_card(rank, suit)}")
        
        # Player's second card
        card_data = self.receive_card()
        if not card_data:
            return False
        result, rank, suit = card_data
        self.player_hand.append((rank, suit))
        print(f"{Colors.DIM}  ├─{Colors.RESET} You receive: {format_card(rank, suit)}")
        
        # Dealer's visible card
        card_data = self.receive_card()
        if not card_data:
            return False
        result, rank, suit = card_data
        self.dealer_hand.append((rank, suit))
        print(f"{Colors.DIM}  └─{Colors.RESET} Dealer shows: {format_card(rank, suit)} {Colors.DIM}(one card hidden){Colors.RESET}")
        
        # Check for Blackjack (21 on initial deal)
        player_value = self.calculate_hand_value(self.player_hand)
        if player_value == 21:
            print(f"\n{Colors.MINT}★ BLACKJACK! ★{Colors.RESET}")
            print(f"{Colors.MINT}You got 21 on the initial deal!{Colors.RESET}\n")
            
            # Receive win result from server
            card_data = self.receive_card()
            if card_data:
                result, rank, suit = card_data
                if result == RESULT_WIN:
                    self.wins += 1
                    print(f"{Colors.MINT}✓ You win!{Colors.RESET}")
            return True
        
        # Player's turn
        print(f"\n{Colors.LAVENDER}┌─ Your Turn ─────────────────────────────────────────┐{Colors.RESET}")
        while True:
            player_value = self.calculate_hand_value(self.player_hand)
            
            # Display cards as ASCII art
            print(f"\n{Colors.DIM}│{Colors.RESET} Your hand:")
            card_art = self.format_hand(self.player_hand)
            for line in card_art.split('\n'):
                print(f"{Colors.DIM}│{Colors.RESET} {line}")
            print(f"{Colors.DIM}│{Colors.RESET} Total: {Colors.BOLD}{player_value}{Colors.RESET}")
            
            if player_value > 21:
                print(f"{Colors.LAVENDER}└─────────────────────────────────────────────────────┘{Colors.RESET}")
                print(f"\n{Colors.ROSE}  ✗ Bust! Over 21{Colors.RESET}")
                self.losses += 1
                # Receive final result from server
                card_data = self.receive_card()
                return True
            
            decision = self.get_user_decision()
            self.send_decision(decision)
            
            if decision == DECISION_STAND:
                print(f"{Colors.LAVENDER}└─────────────────────────────────────────────────────┘{Colors.RESET}")
                print(f"\n{Colors.SAGE}  You stand with {player_value}{Colors.RESET}")
                break
            else:
                # Receive new card
                card_data = self.receive_card()
                if not card_data:
                    return False
                result, rank, suit = card_data
                
                # Check if this is the result message (rank=0 means no card)
                if rank == 0:
                    # This is a result-only message
                    if result == RESULT_LOSS:
                        print(f"{Colors.LAVENDER}└─────────────────────────────────────────────────────┘{Colors.RESET}")
                        print(f"\n{Colors.ROSE}  ✗ Bust! Over 21{Colors.RESET}")
                        self.losses += 1
                    return True
                
                self.player_hand.append((rank, suit))
                print(f"{Colors.DIM}│{Colors.RESET} {Colors.MINT}+{Colors.RESET} Drawing {format_card(rank, suit)}...")
        
        # Dealer's turn
        print(f"\n{Colors.SAGE}┌─ Dealer's Turn ─────────────────────────────────────┐{Colors.RESET}")
        
        # Receive dealer's hidden card
        card_data = self.receive_card()
        if not card_data:
            return False
        result, rank, suit = card_data
        self.dealer_hand.append((rank, suit))
        print(f"{Colors.DIM}│{Colors.RESET} Dealer reveals: {format_card(rank, suit)}")
        
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        # Display dealer's cards as ASCII art
        print(f"{Colors.DIM}│{Colors.RESET} Dealer hand:")
        card_art = self.format_hand(self.dealer_hand)
        for line in card_art.split('\n'):
            print(f"{Colors.DIM}│{Colors.RESET} {line}")
        print(f"{Colors.DIM}│{Colors.RESET} Total: {dealer_value}")
        
        # Receive additional dealer cards
        while True:
            card_data = self.receive_card()
            if not card_data:
                return False
            result, rank, suit = card_data
            
            # If rank is 0, this is the final result
            if rank == 0:
                break
            
            self.dealer_hand.append((rank, suit))
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            print(f"{Colors.DIM}│{Colors.RESET} {Colors.MINT}+{Colors.RESET} Drawing {format_card(rank, suit)}...")
            
            # Show updated hand
            print(f"{Colors.DIM}│{Colors.RESET} Dealer hand:")
            card_art = self.format_hand(self.dealer_hand)
            for line in card_art.split('\n'):
                print(f"{Colors.DIM}│{Colors.RESET} {line}")
            print(f"{Colors.DIM}│{Colors.RESET} Total: {dealer_value}")
            
            if dealer_value >= 17:
                # Next message should be result
                card_data = self.receive_card()
                if not card_data:
                    return False
                result, rank, suit = card_data
                break
        
        # Display final result
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        
        print(f"{Colors.SAGE}└─────────────────────────────────────────────────────┘{Colors.RESET}\n")
        print(f"{Colors.POWDER_BLUE}  ╭─ Final Hands {'─'*37}╮{Colors.RESET}")
        
        # Display player's hand
        print(f"{Colors.POWDER_BLUE}  │{Colors.RESET} {Colors.BOLD}Your Hand:{Colors.RESET} (Total: {Colors.BOLD}{player_value}{Colors.RESET})")
        player_card_art = self.format_hand(self.player_hand)
        for line in player_card_art.split('\n'):
            print(f"{Colors.POWDER_BLUE}  │{Colors.RESET} {line}")
        
        print(f"{Colors.POWDER_BLUE}  ├{'─'*53}┤{Colors.RESET}")
        
        # Display dealer's hand
        print(f"{Colors.POWDER_BLUE}  │{Colors.RESET} {Colors.BOLD}Dealer's Hand:{Colors.RESET} (Total: {Colors.BOLD}{dealer_value}{Colors.RESET})")
        dealer_card_art = self.format_hand(self.dealer_hand)
        for line in dealer_card_art.split('\n'):
            print(f"{Colors.POWDER_BLUE}  │{Colors.RESET} {line}")
        
        print(f"{Colors.POWDER_BLUE}  ╰{'─'*53}╯{Colors.RESET}")
        
        # Display result with big ASCII art and beep
        if result == RESULT_WIN:
            print("\a")  # Beep sound!
            print(f"\n{Colors.MINT}")
            print("  ╔═════════════════════════════════════════════════════╗")
            print("  ║                                                     ║")
            print("  ║          ★  Y O U   W I N !  ★                      ║")
            print("  ║                                                     ║")
            print("  ╚═════════════════════════════════════════════════════╝")
            print(f"{Colors.RESET}")
            self.wins += 1
        elif result == RESULT_LOSS:
            print("\a")  # Beep sound
            print(f"\n{Colors.ROSE}")
            print("  ┌─────────────────────────────────────────────────────┐")
            print("  │                   You Lose                          │")
            print("  └─────────────────────────────────────────────────────┘")
            print(f"{Colors.RESET}")
            self.losses += 1
        elif result == RESULT_TIE:
            print(f"\n{Colors.PEACH}")
            print("  ╭─────────────────────────────────────────────────────╮")
            print("  │                 It's a Tie                          │")
            print("  ╰─────────────────────────────────────────────────────╯")
            print(f"{Colors.RESET}")
            self.ties += 1
        
        return True
    
    def play_all_rounds(self):
        """
        Play all requested rounds.
        
        Returns:
            bool: True if all rounds completed successfully
        """
        print(f"\n{Colors.POWDER_BLUE}╭{'─'*58}╮{Colors.RESET}")
        rounds_text = f"Starting {self.num_rounds} rounds of Blackjack"
        padding = 58 - len(rounds_text) - 1
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET} {Colors.BOLD}{rounds_text}{Colors.RESET}{' '*padding}{Colors.POWDER_BLUE}│{Colors.RESET}")
        print(f"{Colors.POWDER_BLUE}╰{'─'*58}╯{Colors.RESET}")
        
        for round_num in range(1, self.num_rounds + 1):
            if not self.play_round(round_num):
                print(f"{Colors.ROSE}Error in round {round_num}, ending game{Colors.RESET}")
                return False
        
        return True
    
    def show_final_stats(self):
        """Display final game statistics."""
        print(f"\n{Colors.POWDER_BLUE}╭{'─'*58}╮{Colors.RESET}")
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.BOLD}Game Complete{Colors.RESET}{' '*(43)}{Colors.POWDER_BLUE}│{Colors.RESET}")
        print(f"{Colors.POWDER_BLUE}├{'─'*58}┤{Colors.RESET}")
        
        rounds_text = f"Rounds: {self.num_rounds}"
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.DIM}{rounds_text}{Colors.RESET}{' '*(56-len(rounds_text))}{Colors.POWDER_BLUE}│{Colors.RESET}")
        
        wins_text = f"Wins:   {self.wins}"
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.MINT}{wins_text}{Colors.RESET}{' '*(56-len(wins_text))}{Colors.POWDER_BLUE}│{Colors.RESET}")
        
        losses_text = f"Losses: {self.losses}"
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.ROSE}{losses_text}{Colors.RESET}{' '*(56-len(losses_text))}{Colors.POWDER_BLUE}│{Colors.RESET}")
        
        ties_text = f"Ties:   {self.ties}"
        print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.PEACH}{ties_text}{Colors.RESET}{' '*(56-len(ties_text))}{Colors.POWDER_BLUE}│{Colors.RESET}")
        
        if self.wins + self.losses > 0:
            win_rate = (self.wins / (self.wins + self.losses)) * 100
            win_rate_str = f"Win Rate: {win_rate:.1f}%"
            print(f"{Colors.POWDER_BLUE}├{'─'*58}┤{Colors.RESET}")
            print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.BOLD}{win_rate_str}{Colors.RESET}{' '*(56-len(win_rate_str))}{Colors.POWDER_BLUE}│{Colors.RESET}")
            
            # Fun message based on win rate
            if win_rate >= 70:
                msg = "Incredible! Blackjack Master!"
                print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.MINT}{msg}{Colors.RESET}{' '*(56-len(msg))}{Colors.POWDER_BLUE}│{Colors.RESET}")
            elif win_rate >= 50:
                msg = "Great job! You beat the house!"
                print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.SAGE}{msg}{Colors.RESET}{' '*(56-len(msg))}{Colors.POWDER_BLUE}│{Colors.RESET}")
            elif win_rate >= 30:
                msg = "Not bad! Room for improvement"
                print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.PEACH}{msg}{Colors.RESET}{' '*(56-len(msg))}{Colors.POWDER_BLUE}│{Colors.RESET}")
            else:
                msg = "Better luck next time!"
                print(f"{Colors.POWDER_BLUE}│{Colors.RESET}  {Colors.LAVENDER}{msg}{Colors.RESET}{' '*(56-len(msg))}{Colors.POWDER_BLUE}│{Colors.RESET}")
        
        print(f"{Colors.POWDER_BLUE}╰{'─'*58}╯{Colors.RESET}\n")
    
    def close(self):
        """Close the TCP connection."""
        if self.tcp_socket:
            self.tcp_socket.close()

# ============================================================================
# SERVER DISCOVERY
# ============================================================================

def discover_server():
    """
    Listen for server offer messages via UDP.
    
    Returns:
        tuple: (server_ip, server_port, server_name) or None
    """
    print(f"{Colors.LAVENDER}Listening for server offers...{Colors.RESET}\n")
    
    # Create UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Enable SO_REUSEPORT for running multiple clients on same machine
    try:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    except AttributeError:
        # SO_REUSEPORT might not be available on Windows
        pass
    
    # Bind to Wi-Fi adapter for UDP discovery
    wifi_ip = get_local_ip()
    try:
        udp_socket.bind((wifi_ip, OFFER_PORT))
    except:
        # Fallback to all interfaces if Wi-Fi bind fails
        udp_socket.bind(('', OFFER_PORT))
    
    udp_socket.settimeout(UDP_TIMEOUT)
    
    try:
        while True:
            try:
                data, addr = udp_socket.recvfrom(1024)
                server_ip = addr[0]
                
                # Parse offer message
                parsed = parse_offer_message(data)
                if parsed:
                    tcp_port, server_name = parsed
                    print(f"{Colors.MINT}✓ Found server: {server_name}{Colors.RESET}")
                    print(f"{Colors.DIM}  IP: {server_ip}{Colors.RESET}")
                    print(f"{Colors.DIM}  Port: {tcp_port}{Colors.RESET}\n")
                    
                    udp_socket.close()
                    return (server_ip, tcp_port, server_name)
                else:
                    print(f"{Colors.DIM}  Received invalid offer from {server_ip}{Colors.RESET}")
                    
            except socket.timeout:
                print(f"{Colors.DIM}  Still listening...{Colors.RESET}")
                continue
                
    except KeyboardInterrupt:
        print(f"\n{Colors.PEACH}Discovery cancelled{Colors.RESET}")
        udp_socket.close()
        return None
    except Exception as e:
        print(f"{Colors.ROSE}Discovery error: {e}{Colors.RESET}")
        udp_socket.close()
        return None

# ============================================================================
# MAIN
# ============================================================================

def get_num_rounds():
    """
    Prompt user for number of rounds.
    
    Returns:
        int: Number of rounds
    """
    while True:
        try:
            num_rounds = int(input(f"{Colors.PEACH}How many rounds would you like to play? {Colors.RESET}"))
            if num_rounds > 0 and num_rounds <= 255:
                return num_rounds
            else:
                print(f"{Colors.DIM}  Please enter a number between 1 and 255{Colors.RESET}")
        except ValueError:
            print(f"{Colors.DIM}  Please enter a valid number{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.PEACH}Exiting...{Colors.RESET}")
            sys.exit(0)


def main():
    """Main client entry point."""
    print(f"\n{Colors.POWDER_BLUE}")
    print("  ╭──────────────────────────────────────────────────────╮")
    print("  │                                                      │")
    print(f"  │  {Colors.BOLD}  Blackjack Client - Rasengan Gamblers  {Colors.RESET}{Colors.POWDER_BLUE}            │")
    print("  │                                                      │")
    print("  ╰──────────────────────────────────────────────────────╯")
    print(f"{Colors.RESET}\n")
    
    # Get number of rounds from user
    num_rounds = get_num_rounds()
    print()
    
    while True:
        # Discover server
        server_info = discover_server()
        
        if not server_info:
            print(f"{Colors.ROSE}Failed to discover server{Colors.RESET}")
            break
        
        server_ip, server_port, server_name = server_info
        
        # Create client and connect
        client = BlackjackClient(server_ip, server_port, server_name, num_rounds)
        
        if not client.connect():
            print(f"{Colors.ROSE}Failed to connect to server{Colors.RESET}")
            client.close()
            break
        
        # Play all rounds
        if client.play_all_rounds():
            client.show_final_stats()
        
        # Close connection
        client.close()
        
        # Ask if user wants to play again
        print(f"\n{Colors.LAVENDER}Looking for another game...{Colors.RESET}\n")
        time.sleep(2)
        
        # Get new number of rounds for next game
        num_rounds = get_num_rounds()
        print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.PEACH}Client shutting down...{Colors.RESET}")
        print(f"{Colors.MINT}Goodbye! ✨{Colors.RESET}\n")
