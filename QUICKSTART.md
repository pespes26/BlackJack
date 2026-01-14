# 🎰 Quick Start Guide

## Running the Project

### 1. Test the Protocol (Optional but Recommended)
```bash
cd C:\Users\barpe\Desktop\blackjack
python test_protocol.py
```

You should see:
```
✓ ALL TESTS PASSED!
```

### 2. Start the Server
Open a terminal and run:
```bash
cd C:\Users\barpe\Desktop\blackjack
python blackjack_server.py
```

The server will:
- Display its IP address
- Start broadcasting UDP offers every second
- Wait for client connections

### 3. Start the Client
Open another terminal and run:
```bash
cd C:\Users\barpe\Desktop\blackjack
python blackjack_client.py
```

The client will:
1. Ask how many rounds you want to play
2. Discover the server automatically
3. Connect and start playing
4. Show your cards and prompt for decisions (H for Hit, S for Stand)
5. Display results and statistics
6. Loop back to discover servers again

### 4. Play Multiple Clients (Optional)
You can run multiple clients on the same machine - they'll all discover the same server and play concurrently!

## Game Tips
- Cards: Number = face value, J/Q/K = 10, Ace = 11
- Goal: Get closer to 21 than dealer without going over
- **Hit**: Take another card
- **Stand**: Keep your current hand
- Dealer hits until 17 or higher

## Customization
Want to change team names?
- **Server**: Edit line 21 in `blackjack_server.py`
- **Client**: Edit line 21 in `blackjack_client.py`

## Troubleshooting

### Can't find the server?
- Make sure server is running first
- Check firewall settings
- Server and client should be on the same network

### Connection timeout?
- Server might be busy with other clients
- Try restarting both server and client

### Protocol errors?
- Run `python test_protocol.py` to verify implementation
- Check that both client and server are using the same protocol version

## For the Hackathon

1. **Test with other teams**: Your server should work with their clients and vice versa!
2. **Set up Git**: Initialize a repository and commit regularly
3. **Network coordination**: Use the shared testing network during the event
4. **Be creative**: Customize your team name for the contest!

Good luck! 🎰🃏
