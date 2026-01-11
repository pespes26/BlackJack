# 🎰 Blackjack Network Game - Royal Flush Dealers vs Ace High Legends 🃏

A client-server Blackjack game implementation for the "Intro to Networks 2025" hackathon assignment. Features UDP server discovery, TCP gameplay, and colorful terminal output!

## 🎯 Features

### Server
- **UDP Broadcast**: Automatically announces presence on the network every second
- **Multi-client Support**: Handles multiple concurrent players using threading
- **Full Blackjack Logic**: Implements dealer AI (hits until 17), bust detection, and winner determination
- **Colorful Output**: Beautiful ANSI-colored terminal display
- **Standard 52-card Deck**: Proper deck management with auto-shuffle

### Client
- **Automatic Server Discovery**: Listens for UDP broadcasts on port 13122
- **Interactive Gameplay**: User-friendly prompts for hit/stand decisions
- **Beautiful Card Display**: Color-coded cards (red for ♥♦, black for ♣♠)
- **Statistics Tracking**: Tracks wins, losses, ties, and win rate
- **Auto-reconnect**: Automatically returns to server discovery after completing rounds

## 📋 Protocol Specification

### Message Types
- **Offer (UDP)**: Server → Client broadcast (39 bytes)
- **Request (TCP)**: Client → Server connection (38 bytes)
- **Payload (TCP)**: Bidirectional game messages (9-10 bytes)

All messages start with magic cookie `0xabcddcba` for validation.

## 🚀 Quick Start

### Running the Server

```bash
python blackjack_server.py
```

The server will:
1. Display its IP address
2. Start broadcasting UDP offers on port 13122
3. Listen for TCP connections on an automatically assigned port

### Running the Client

```bash
python blackjack_client.py
```

The client will:
1. Ask how many rounds you want to play
2. Listen for server offers
3. Connect to the first discovered server
4. Play the requested number of rounds
5. Display statistics and return to discovery mode

## 📁 Project Structure

```
blackjack/
├── blackjack_protocol.py   # Shared protocol definitions and packet encoding/decoding
├── blackjack_server.py      # Server with UDP broadcast and TCP game logic
├── blackjack_client.py      # Client with discovery and interactive gameplay
└── README.md                # This file
```

## 🎮 Game Rules

- **Card Values**: Number cards = face value, Face cards (J/Q/K) = 10, Ace = 11
- **Objective**: Get closer to 21 than the dealer without going over
- **Player Turn**: Hit (take card) or Stand (keep hand)
- **Dealer Turn**: Must hit until reaching 17 or higher
- **Winning**: Player > Dealer (or dealer busts) = Win
- **Losing**: Player < Dealer (or player busts) = Loss
- **Tie**: Same total = Tie

## 🔧 Technical Details

### No Busy Waiting
All network operations use proper blocking calls or timeouts - CPU usage stays minimal.

### Thread Safety
Server uses daemon threads for each client connection, allowing concurrent games.

### Error Handling
- Invalid packets are rejected (magic cookie validation)
- Timeouts on all network operations
- Graceful handling of disconnections
- Proper socket cleanup

### Network Configuration
- **UDP Port**: 13122 (hardcoded for client discovery)
- **TCP Port**: Dynamically assigned by OS
- **SO_REUSEPORT**: Enabled on client for running multiple instances

## 🎨 Code Quality

- ✅ Extensive comments and documentation
- ✅ No hard-coded IP addresses or ports in game logic
- ✅ Meaningful variable and function names
- ✅ Proper error handling with return value checks
- ✅ Clean separation of concerns (protocol, server, client)

## 🧪 Testing

### Test Server Discovery
1. Start server
2. Start multiple clients on different machines
3. Verify all clients receive offers

### Test Gameplay
1. Play several rounds
2. Test hit until bust
3. Test stand functionality
4. Verify dealer hits to 17
5. Check win/loss/tie calculations

### Test Error Handling
1. Send invalid packets
2. Disconnect during gameplay
3. Test timeout scenarios

## 🏆 Team Names

- **Server**: 🎰 Royal Flush Dealers 🎰
- **Client**: 🃏 Ace High Legends 🃏

Feel free to change these in the source code to your own creative names!

## 📝 Requirements

- Python 3.x
- Standard library only (no external dependencies)
- Works on Windows, Linux, and macOS

## 🎓 Assignment Compliance

This implementation meets all requirements specified in the hackathon assignment:
- ✅ UDP broadcast for server offers (port 13122)
- ✅ TCP for gameplay with proper packet formats
- ✅ Magic cookie validation (0xabcddcba)
- ✅ All message types (Offer, Request, Payload)
- ✅ Full Blackjack game logic
- ✅ Multiple rounds support
- ✅ Win rate calculation and display
- ✅ Concurrent client handling
- ✅ No busy waiting
- ✅ Proper timeout and error handling
- ✅ Extensive code comments

## 🎯 Excellence Criteria

- ✅ Works with any compliant client/server
- ✅ High-quality, well-commented code
- ✅ Proper error handling for invalid inputs and timeouts
- ✅ Fun, colorful output with card symbols
- ✅ Interesting statistics tracking
- ✅ No hard-coded network constants
- ✅ Clean architecture with separated concerns

## 📜 License

Created for the "Intro to Networks 2025" hackathon assignment.

---

**Good luck, and may your cards always add up to 21!** 🎰🃏
