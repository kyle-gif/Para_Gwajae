from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError
from models import User, UserInDB
from schemas import UserCreate, UserLogin, Token
from database import user_collection
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(email=user.email, hashed_password=hashed_password)
    try:
        user_collection.insert_one(user_in_db.dict(by_alias=True))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return user_in_db

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = user_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    email = decode_access_token(token)
    user = user_collection.find_one({"email": email})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user)
