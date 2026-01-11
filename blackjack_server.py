#!/usr/bin/env python3
"""
Blackjack Server
Broadcasts UDP offer messages and handles TCP connections for playing Blackjack.
"""

import socket
import struct
import random
import threading
import time
import sys
from blackjack_protocol import *

# ============================================================================
# ANSI COLOR CODES FOR PRETTY OUTPUT
# ============================================================================

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

# ============================================================================
# CONFIGURATION
# ============================================================================

SERVER_NAME = "🍃 Leaf Village Casino 🍃"  # Where ninjas bet it all!
TCP_PORT = 0  # 0 means OS will assign a random available port
OFFER_INTERVAL = 1.0  # Send offer every 1 second
TCP_TIMEOUT = 60.0  # TCP connection timeout

# ============================================================================
# DECK AND CARD MANAGEMENT
# ============================================================================

class Deck:
    """Represents a standard 52-card deck."""
    
    def __init__(self):
        """Initialize and shuffle a new deck."""
        self.cards = []
        self.reset()
    
    def reset(self):
        """Reset and shuffle the deck with all 52 cards."""
        self.cards = []
        # Create all combinations of ranks (1-13) and suits (0-3)
        for suit in range(4):
            for rank in range(1, 14):
                self.cards.append((rank, suit))
        random.shuffle(self.cards)
    
    def draw(self):
        """
        Draw a card from the deck.
        
        Returns:
            tuple: (rank, suit) or None if deck is empty
        """
        if not self.cards:
            self.reset()  # Auto-reset if we run out
        return self.cards.pop() if self.cards else None

# ============================================================================
# BLACKJACK GAME LOGIC
# ============================================================================

class BlackjackGame:
    """Manages a single Blackjack game session."""
    
    def __init__(self, client_socket, client_address, client_name, num_rounds):
        """
        Initialize a new game session.
        
        Args:
            client_socket: TCP socket connected to client
            client_address: Client address tuple
            client_name (str): Client team name
            num_rounds (int): Number of rounds to play
        """
        self.client_socket = client_socket
        self.client_address = client_address
        self.client_name = client_name
        self.num_rounds = num_rounds
        self.deck = Deck()
        
        self.player_hand = []
        self.dealer_hand = []
    
    def send_card(self, rank, suit, result=RESULT_NOT_OVER):
        """
        Send a card to the client.
        
        Args:
            rank (int): Card rank (1-13)
            suit (int): Card suit (0-3)
            result (int): Round result status
        """
        message = create_server_payload(result, rank, suit)
        self.client_socket.sendall(message)
    
    def receive_decision(self):
        """
        Receive a decision from the client.
        
        Returns:
            str: "Hittt" or "Stand" or None if error
        """
        try:
            data = self.client_socket.recv(10)
            if not data:
                return None
            return parse_client_payload(data)
        except socket.timeout:
            print(f"{Colors.RED}Client decision timeout{Colors.RESET}")
            return None
        except Exception as e:
            print(f"{Colors.RED}Error receiving decision: {e}{Colors.RESET}")
            return None
    
    def calculate_hand_value(self, hand):
        """
        Calculate the total value of a hand.
        
        Args:
            hand (list): List of (rank, suit) tuples
            
        Returns:
            int: Total hand value
        """
        total = sum(get_card_value(rank) for rank, suit in hand)
        return total
    
    def format_hand(self, hand, hide_second=False):
        """
        Format a hand for display.
        
        Args:
            hand (list): List of (rank, suit) tuples
            hide_second (bool): Whether to hide the second card
            
        Returns:
            str: Formatted hand string
        """
        if hide_second and len(hand) > 1:
            cards = [format_card(*hand[0]), "🂠"]
        else:
            cards = [format_card(rank, suit) for rank, suit in hand]
        return " ".join(cards)
    
    def play_round(self, round_num):
        """
        Play a single round of Blackjack.
        
        Args:
            round_num (int): Current round number (for display)
            
        Returns:
            str: "win", "loss", or "tie"
        """
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Round {round_num}/{self.num_rounds}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        
        # Reset hands
        self.player_hand = []
        self.dealer_hand = []
        
        # Initial deal: 2 cards to player, 2 to dealer
        print(f"{Colors.YELLOW}Dealing initial cards...{Colors.RESET}")
        
        for _ in range(2):
            card = self.deck.draw()
            self.player_hand.append(card)
            self.send_card(*card, RESULT_NOT_OVER)
            print(f"  → Player gets {format_card(*card)}")
        
        for _ in range(2):
            card = self.deck.draw()
            self.dealer_hand.append(card)
        
        # Show dealer's first card (second is hidden)
        self.send_card(*self.dealer_hand[0], RESULT_NOT_OVER)
        print(f"  → Dealer shows {format_card(*self.dealer_hand[0])} (one card hidden)")
        
        player_value = self.calculate_hand_value(self.player_hand)
        print(f"\n{Colors.WHITE}Player hand: {self.format_hand(self.player_hand)} = {player_value}{Colors.RESET}")
        print(f"{Colors.WHITE}Dealer hand: {self.format_hand(self.dealer_hand, hide_second=True)}{Colors.RESET}")
        
        # Player's turn
        print(f"\n{Colors.MAGENTA}Player's turn...{Colors.RESET}")
        while True:
            decision = self.receive_decision()
            
            if decision is None:
                print(f"{Colors.RED}Failed to receive decision, ending round{Colors.RESET}")
                return "loss"
            
            print(f"  Player decision: {Colors.BOLD}{decision}{Colors.RESET}")
            
            if decision == DECISION_STAND:
                break
            elif decision == DECISION_HIT:
                card = self.deck.draw()
                self.player_hand.append(card)
                self.send_card(*card, RESULT_NOT_OVER)
                player_value = self.calculate_hand_value(self.player_hand)
                print(f"  → Player gets {format_card(*card)}, hand = {self.format_hand(self.player_hand)} = {player_value}")
                
                # Check for bust
                if player_value > 21:
                    print(f"{Colors.RED}Player BUSTS!{Colors.RESET}")
                    self.send_card(0, 0, RESULT_LOSS)  # Send loss result
                    return "loss"
            else:
                print(f"{Colors.RED}Invalid decision received: {decision}{Colors.RESET}")
        
        # Dealer's turn
        print(f"\n{Colors.MAGENTA}Dealer's turn...{Colors.RESET}")
        print(f"  Dealer reveals hidden card: {format_card(*self.dealer_hand[1])}")
        
        # Reveal dealer's second card to client
        self.send_card(*self.dealer_hand[1], RESULT_NOT_OVER)
        
        dealer_value = self.calculate_hand_value(self.dealer_hand)
        print(f"  Dealer hand: {self.format_hand(self.dealer_hand)} = {dealer_value}")
        
        # Dealer hits until 17 or more
        while dealer_value < 17:
            print(f"  Dealer has {dealer_value}, must hit...")
            card = self.deck.draw()
            self.dealer_hand.append(card)
            self.send_card(*card, RESULT_NOT_OVER)
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            print(f"  → Dealer gets {format_card(*card)}, hand = {self.format_hand(self.dealer_hand)} = {dealer_value}")
        
        # Determine winner
        print(f"\n{Colors.BOLD}Final hands:{Colors.RESET}")
        print(f"  Player: {self.format_hand(self.player_hand)} = {player_value}")
        print(f"  Dealer: {self.format_hand(self.dealer_hand)} = {dealer_value}")
        
        if dealer_value > 21:
            print(f"{Colors.GREEN}Dealer BUSTS! Player wins!{Colors.RESET}")
            self.send_card(0, 0, RESULT_WIN)
            return "win"
        elif player_value > dealer_value:
            print(f"{Colors.GREEN}Player wins!{Colors.RESET}")
            self.send_card(0, 0, RESULT_WIN)
            return "win"
        elif dealer_value > player_value:
            print(f"{Colors.RED}Dealer wins!{Colors.RESET}")
            self.send_card(0, 0, RESULT_LOSS)
            return "loss"
        else:
            print(f"{Colors.YELLOW}It's a tie!{Colors.RESET}")
            self.send_card(0, 0, RESULT_TIE)
            return "tie"
    
    def play_all_rounds(self):
        """Play all rounds and track results."""
        print(f"\n{Colors.GREEN}{'*'*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Starting game with {self.client_name}{Colors.RESET}")
        print(f"{Colors.GREEN}{'*'*60}{Colors.RESET}")
        print(f"Client: {self.client_address}")
        print(f"Rounds: {self.num_rounds}")
        
        wins = 0
        losses = 0
        ties = 0
        
        for round_num in range(1, self.num_rounds + 1):
            try:
                result = self.play_round(round_num)
                if result == "win":
                    wins += 1
                elif result == "loss":
                    losses += 1
                else:
                    ties += 1
            except Exception as e:
                print(f"{Colors.RED}Error in round {round_num}: {e}{Colors.RESET}")
                break
        
        print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}Game Over - Final Results{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")
        print(f"Wins: {Colors.GREEN}{wins}{Colors.RESET}")
        print(f"Losses: {Colors.RED}{losses}{Colors.RESET}")
        print(f"Ties: {Colors.YELLOW}{ties}{Colors.RESET}")
        
        if wins + losses > 0:
            win_rate = (wins / (wins + losses)) * 100
            print(f"Player win rate: {Colors.BOLD}{win_rate:.1f}%{Colors.RESET}")

# ============================================================================
# TCP SERVER
# ============================================================================

def handle_client(client_socket, client_address):
    """
    Handle a single client connection.
    
    Args:
        client_socket: TCP socket for the client
        client_address: Client address tuple
    """
    try:
        client_socket.settimeout(TCP_TIMEOUT)
        
        # Receive request message
        data = client_socket.recv(38)
        if not data:
            print(f"{Colors.RED}No data received from {client_address}{Colors.RESET}")
            return
        
        parsed = parse_request_message(data)
        if not parsed:
            print(f"{Colors.RED}Invalid request from {client_address}{Colors.RESET}")
            return
        
        num_rounds, client_name = parsed
        
        # Play the game
        game = BlackjackGame(client_socket, client_address, client_name, num_rounds)
        game.play_all_rounds()
        
    except socket.timeout:
        print(f"{Colors.RED}Connection timeout with {client_address}{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error handling client {client_address}: {e}{Colors.RESET}")
    finally:
        client_socket.close()
        print(f"{Colors.YELLOW}Connection closed with {client_address}{Colors.RESET}\n")


def run_tcp_server(tcp_port):
    """
    Run the TCP server to accept client connections.
    
    Args:
        tcp_port (int): Port to listen on
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('', tcp_port))
    server_socket.listen(5)
    
    actual_port = server_socket.getsockname()[1]
    print(f"{Colors.GREEN}TCP server listening on port {actual_port}{Colors.RESET}")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"\n{Colors.BLUE}New connection from {client_address}{Colors.RESET}")
            
            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Colors.RED}Error accepting connection: {e}{Colors.RESET}")
    
    server_socket.close()

# ============================================================================
# UDP BROADCAST
# ============================================================================

def run_udp_broadcast(tcp_port):
    """
    Continuously broadcast offer messages via UDP.
    
    Args:
        tcp_port (int): The TCP port to advertise
    """
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    offer_message = create_offer_message(tcp_port, SERVER_NAME)
    broadcast_address = (get_broadcast_address(), OFFER_PORT)
    
    print(f"{Colors.GREEN}Broadcasting offer messages to {broadcast_address}{Colors.RESET}")
    print(f"{Colors.GREEN}Server name: {SERVER_NAME}{Colors.RESET}\n")
    
    while True:
        try:
            broadcast_socket.sendto(offer_message, broadcast_address)
            time.sleep(OFFER_INTERVAL)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Colors.RED}Error broadcasting: {e}{Colors.RESET}")
            time.sleep(OFFER_INTERVAL)
    
    broadcast_socket.close()

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main server entry point."""
    print(f"\n{Colors.BOLD}{Colors.MAGENTA}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          🎰 BLACKJACK SERVER - ROYAL FLUSH DEALERS 🎰      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"{Colors.BOLD}Server started, listening on IP address {local_ip}{Colors.RESET}\n")
    
    # Create TCP server socket to get assigned port
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen(5)
    actual_tcp_port = tcp_socket.getsockname()[1]
    tcp_socket.close()
    
    # Start UDP broadcast thread
    broadcast_thread = threading.Thread(
        target=run_udp_broadcast,
        args=(actual_tcp_port,),
        daemon=True
    )
    broadcast_thread.start()
    
    # Run TCP server in main thread
    try:
        run_tcp_server(actual_tcp_port)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Server shutting down...{Colors.RESET}")
    
    print(f"{Colors.GREEN}Goodbye!{Colors.RESET}\n")


if __name__ == "__main__":
    main()
