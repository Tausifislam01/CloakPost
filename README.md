# CloakPost - Secure Messaging Platform

A secure messaging platform built with Django, featuring end-to-end encryption, self-destructing messages, and real-time chat capabilities.

## Features

- End-to-end encrypted messaging using AES-GCM
- Real-time chat using Django Channels and WebSockets
- Self-destructing messages (auto-delete after 5 minutes)
- User authentication and friend system
- Post sharing with visibility controls

## Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd cloakpost
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start Redis server:
```bash
redis-server
```

6. Start the development server:
```bash
python manage.py runserver
# OR for production-like setup:
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

## Architecture

- Django 5.2.7 for backend
- Django Channels for WebSocket support
- Redis for message broker
- Daphne as ASGI server
- AES-GCM for message encryption
- Tailwind CSS for styling

## Security Features

- End-to-end encryption for all messages
- Messages auto-delete after being read
- CSRF protection
- XSS protection via content security policy
- Secure session handling
- Input validation and sanitization

## API Documentation

### Messages

- `GET /msg/threads/` - List user's message threads
- `POST /msg/dm/{user_id}/` - Start or resume 1:1 chat
- `GET /msg/threads/{thread_id}/messages/` - Get messages in thread
- WebSocket: `ws://.../ws/threads/{thread_id}/` - Real-time chat connection

### Posts

- `GET /posts/` - List public posts
- `POST /posts/` - Create new post
- Post visibility controls: public/private

### Users

- User authentication endpoints
- Friend request system
- Profile management

## Development

- Use `python manage.py test` to run tests
- Run `python manage.py cleanup_empty_threads` to clean duplicate threads
- Frontend templates in `templates/` directory
- Static files in `static/` directory