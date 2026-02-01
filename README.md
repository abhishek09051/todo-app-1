# todo-app-1

A full-stack todo application with React frontend, Python FastAPI backend, PostgreSQL database, and Google OAuth authentication.

## Features

- ✅ Create, read, update, and delete todos
- ✅ Mark todos as completed
- ✅ Google OAuth 2.0 authentication
- ✅ JWT-based session management
- ✅ Protected routes and API endpoints
- ✅ Modern React UI with Vite
- ✅ FastAPI backend with SQLAlchemy ORM
- ✅ PostgreSQL database
- ✅ Fully Dockerized setup

## Tech Stack

- **Frontend**: React 18, Vite
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, JWT
- **Database**: PostgreSQL 15
- **Authentication**: Google OAuth 2.0
- **Containerization**: Docker, Docker Compose

## Getting Started

### Prerequisites

- Docker
- Docker Compose
- Google OAuth 2.0 credentials (Client ID and Secret)

### Setup Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to "Credentials" and create OAuth 2.0 Client ID
5. Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
6. Copy Client ID and Client Secret

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd todo-app-1
```

2. Create `.env` file in the root directory:
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET_KEY=your_random_secret_key_here
```

3. Start the application:
```bash
docker-compose up --build
```

4. Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Development

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Project Structure

```
todo-app-1/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.jsx
│   │   │   └── TodoApp.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── main.jsx
│   │   └── index.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
├── .env
└── README.md
```

## API Endpoints

### Authentication
- `GET /api/auth/google` - Initiate Google OAuth flow
- `GET /api/auth/google/callback` - OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout user

### Todos (Protected)
- `GET /api/todos` - Get all todos for current user
- `POST /api/todos` - Create a new todo
- `GET /api/todos/{id}` - Get a specific todo
- `PUT /api/todos/{id}` - Update a todo
- `DELETE /api/todos/{id}` - Delete a todo

## License

MIT