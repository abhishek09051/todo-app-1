from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
import os
from typing import List, Optional
import jwt
from datetime import datetime, timedelta
import httpx
from urllib.parse import urlencode

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://todouser:todopassword@db:5432/tododb"
)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

GOOGLE_REDIRECT_URI = "http://localhost:8000/api/auth/google/callback"
FRONTEND_URL = "http://localhost"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    google_id = Column(String, unique=True, nullable=False)
    
    todos = relationship("TodoDB", back_populates="owner", cascade="all, delete-orphan")

class TodoDB(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    owner = relationship("UserDB", back_populates="todos")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class User(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str] = None

    class Config:
        from_attributes = True

class TodoCreate(BaseModel):
    title: str
    completed: bool = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: int
    title: str
    completed: bool
    user_id: int

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="Todo API with OAuth")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_current_user(user_id: int = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

# Routes
@app.get("/")
def read_root():
    return {"message": "Todo API with OAuth is running"}

# Authentication routes
@app.get("/api/auth/google")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return {"url": url}

@app.get("/api/auth/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        user_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_info = user_response.json()
    
    # Create or update user
    user = db.query(UserDB).filter(UserDB.google_id == user_info["id"]).first()
    
    if not user:
        user = UserDB(
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
            google_id=user_info["id"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.name = user_info["name"]
        user.picture = user_info.get("picture")
        db.commit()
    
    # Create JWT token
    jwt_token = create_access_token({"user_id": user.id, "email": user.email})
    
    # Redirect to frontend with token
    return RedirectResponse(url=f"{FRONTEND_URL}?token={jwt_token}")

@app.get("/api/auth/me", response_model=User)
def get_me(current_user: UserDB = Depends(get_current_user)):
    return current_user

@app.post("/api/auth/logout")
def logout():
    return {"message": "Logged out successfully"}

# Todo routes (protected)
@app.get("/api/todos", response_model=List[Todo])
def get_todos(current_user: UserDB = Depends(get_current_user), db: Session = Depends(get_db)):
    todos = db.query(TodoDB).filter(TodoDB.user_id == current_user.id).all()
    return todos

@app.post("/api/todos", response_model=Todo)
def create_todo(
    todo: TodoCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_todo = TodoDB(title=todo.title, completed=todo.completed, user_id=current_user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/api/todos/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    todo = db.query(TodoDB).filter(
        TodoDB.id == todo_id,
        TodoDB.user_id == current_user.id
    ).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.put("/api/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    todo = db.query(TodoDB).filter(
        TodoDB.id == todo_id,
        TodoDB.user_id == current_user.id
    ).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    if todo_update.title is not None:
        todo.title = todo_update.title
    if todo_update.completed is not None:
        todo.completed = todo_update.completed
    
    db.commit()
    db.refresh(todo)
    return todo

@app.delete("/api/todos/{todo_id}")
def delete_todo(
    todo_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    todo = db.query(TodoDB).filter(
        TodoDB.id == todo_id,
        TodoDB.user_id == current_user.id
    ).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    db.delete(todo)
    db.commit()
    return {"message": "Todo deleted successfully"}