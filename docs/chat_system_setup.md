# Chat System Setup and Troubleshooting Guide

## Overview
The chat system uses Django Channels with Redis as the backing store for WebSocket communications. This document explains the proper setup and common issues encountered.

## Required Components
1. Python Virtual Environment
2. Redis Server
3. Django with Channels (ASGI server)

## Correct Startup Sequence

### 1. Activate Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Start Redis Server
Redis must be running before starting Django. Use these settings for Windows compatibility:
```powershell
redis-server --maxclients 1000 --protected-mode no
```

### 3. Start Django with Daphne
Use Daphne (ASGI server) instead of the default Django development server for WebSocket support:
```powershell
daphne -b 127.0.0.1 -p 8000 config.asgi:application -v2
```

## Common Issues and Solutions

### 1. "Not connected to chat" Error
This usually occurs when:
- Redis is not running
- WebSocket connection fails
- URL patterns don't match

Solution: Ensure Redis is running first, then start Daphne.

### 2. Redis Connection Issues
If Redis fails to start, try these options:
- Use lower maxclients value (--maxclients 1000)
- Disable protected mode (--protected-mode no)
- Ensure port 6379 is free

### 3. Multiple Empty Threads
If you see multiple empty chat threads being created:
- Use the cleanup command: `python manage.py cleanup_empty_threads`
- Refresh the page only when necessary
- Don't create new threads if one already exists

## System Architecture

### WebSocket Flow
1. Client connects to `/ws/threads/<thread_id>/`
2. Connection authenticated via Django session
3. Messages encrypted before storage
4. Redis handles real-time message broadcasting

### Security Features
- All messages are encrypted (AES-GCM)
- WebSocket connections require authentication
- Redis channel layers are isolated

## Debugging

### Enable Verbose Logging
Run Daphne with `-v2` flag for detailed logs:
```powershell
daphne -b 127.0.0.1 -p 8000 config.asgi:application -v2
```

### Check Redis Connection
```powershell
redis-cli ping
```
Should return "PONG" if Redis is running properly.

## Important URLs
- Chat Interface: http://127.0.0.1:8000/msg/ui/threads/
- WebSocket Endpoint: ws://127.0.0.1:8000/ws/threads/<thread_id>/

## Proper Shutdown Sequence
1. Close Django/Daphne (Ctrl+C)
2. Stop Redis server (Ctrl+C)
3. Deactivate virtual environment (`deactivate`)