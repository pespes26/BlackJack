#!/usr/bin/env python3
"""
Quick test script to verify protocol encoding/decoding works correctly.
Run this before testing the full client-server application.
"""

import sys
sys.path.insert(0, '.')

from blackjack_protocol import *

def test_offer_message():
    """Test offer message encoding/decoding."""
    print("Testing OFFER message...")
    
    # Create offer
    tcp_port = 12345
    server_name = "Test Server"
    offer = create_offer_message(tcp_port, server_name)
    
    # Verify length
    assert len(offer) == 39, f"Offer length should be 39, got {len(offer)}"
    
    # Parse it back
    parsed = parse_offer_message(offer)
    assert parsed is not None, "Failed to parse offer"
    
    parsed_port, parsed_name = parsed
    assert parsed_port == tcp_port, f"Port mismatch: expected {tcp_port}, got {parsed_port}"
    assert parsed_name == server_name, f"Name mismatch: expected '{server_name}', got '{parsed_name}'"
    
    print("  ✓ Offer message encoding/decoding works!")


def test_request_message():
    """Test request message encoding/decoding."""
    print("Testing REQUEST message...")
    
    # Create request
    num_rounds = 5
    client_name = "Test Client"
    request = create_request_message(num_rounds, client_name)
    
    # Verify length
    assert len(request) == 38, f"Request length should be 38, got {len(request)}"
    
    # Parse it back
    parsed = parse_request_message(request)
    assert parsed is not None, "Failed to parse request"
    
    parsed_rounds, parsed_name = parsed
    assert parsed_rounds == num_rounds, f"Rounds mismatch: expected {num_rounds}, got {parsed_rounds}"
    assert parsed_name == client_name, f"Name mismatch: expected '{client_name}', got '{parsed_name}'"
    
    print("  ✓ Request message encoding/decoding works!")


def test_client_payload():
    """Test client payload encoding/decoding."""
    print("Testing CLIENT PAYLOAD message...")
    
    # Test Hit
    hit_msg = create_client_payload(DECISION_HIT)
    assert len(hit_msg) == 10, f"Client payload should be 10 bytes, got {len(hit_msg)}"
    
    parsed = parse_client_payload(hit_msg)
    assert parsed == DECISION_HIT, f"Decision mismatch: expected '{DECISION_HIT}', got '{parsed}'"
    
    # Test Stand
    stand_msg = create_client_payload(DECISION_STAND)
    parsed = parse_client_payload(stand_msg)
    assert parsed == DECISION_STAND, f"Decision mismatch: expected '{DECISION_STAND}', got '{parsed}'"
    
    print("  ✓ Client payload encoding/decoding works!")


def test_server_payload():
    """Test server payload encoding/decoding."""
    print("Testing SERVER PAYLOAD message...")
    
    # Create server payload (Ace of Spades, round not over)
    rank = 1
    suit = SUIT_SPADE
    result = RESULT_NOT_OVER
    
    payload = create_server_payload(result, rank, suit)
    assert len(payload) == 9, f"Server payload should be 9 bytes, got {len(payload)}"
    
    # Parse it back
    parsed = parse_server_payload(payload)
    assert parsed is not None, "Failed to parse server payload"
    
    parsed_result, parsed_rank, parsed_suit = parsed
    assert parsed_result == result, f"Result mismatch: expected {result}, got {parsed_result}"
    assert parsed_rank == rank, f"Rank mismatch: expected {rank}, got {parsed_rank}"
    assert parsed_suit == suit, f"Suit mismatch: expected {suit}, got {parsed_suit}"
    
    print("  ✓ Server payload encoding/decoding works!")


def test_card_values():
    """Test card value calculations."""
    print("Testing CARD VALUES...")
    
    # Test Ace
    assert get_card_value(1) == 11, "Ace should be worth 11"
    
    # Test number cards
    for rank in range(2, 11):
        assert get_card_value(rank) == rank, f"Card {rank} should be worth {rank}"
    
    # Test face cards
    assert get_card_value(11) == 10, "Jack should be worth 10"
    assert get_card_value(12) == 10, "Queen should be worth 10"
    assert get_card_value(13) == 10, "King should be worth 10"
    
    print("  ✓ Card value calculations correct!")


def test_card_formatting():
    """Test card formatting."""
    print("Testing CARD FORMATTING...")
    
    # Test some cards
    assert format_card(1, SUIT_HEART) == "A♥"
    assert format_card(13, SUIT_SPADE) == "K♠"
    assert format_card(10, SUIT_DIAMOND) == "10♦"
    assert format_card(7, SUIT_CLUB) == "7♣"
    
    print("  ✓ Card formatting works!")


def test_name_padding():
    """Test name padding/truncation."""
    print("Testing NAME PADDING...")
    
    # Short name
    short_name = "Bob"
    padded = pad_name(short_name)
    assert len(padded) == NAME_SIZE, f"Padded name should be {NAME_SIZE} bytes"
    assert unpad_name(padded) == short_name, "Short name round-trip failed"
    
    # Exact size name
    exact_name = "A" * NAME_SIZE
    padded = pad_name(exact_name)
    assert len(padded) == NAME_SIZE
    assert unpad_name(padded) == exact_name, "Exact name round-trip failed"
    
    # Long name (should truncate)
    long_name = "A" * (NAME_SIZE + 10)
    padded = pad_name(long_name)
    assert len(padded) == NAME_SIZE
    assert unpad_name(padded) == long_name[:NAME_SIZE], "Long name should be truncated"
    
    print("  ✓ Name padding/truncation works!")


def run_all_tests():
    """Run all protocol tests."""
    print("\n" + "="*60)
    print("BLACKJACK PROTOCOL TEST SUITE")
    print("="*60 + "\n")
    
    try:
        test_offer_message()
        test_request_message()
        test_client_payload()
        test_server_payload()
        test_card_values()
        test_card_formatting()
        test_name_padding()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60 + "\n")
        
        print("Your protocol implementation is working correctly!")
        print("You can now test the full client-server application.\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
