from fastapi import FastAPI, Request, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from dotenv import load_dotenv
import openai
import asyncio

from starlette.responses import JSONResponse

load_dotenv()

app = FastAPI()

# MongoDB 클라이언트 설정
client = MongoClient("mongodb://localhost:27017")
db = client.login_db
users_collection = db.users

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Please enter both username and password")
    users_collection.insert_one({"username": username, "password": password})
    return RedirectResponse(url="/", status_code=303)


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="Please enter both username and password")
    user = users_collection.find_one({"username": username})
    if user and (password == user["password"]):
        return JSONResponse(content={"detail": "Login successful"}, status_code=200)
    return JSONResponse(content={"detail": "Invalid credentials"}, status_code=401)


@app.post("/delete")
async def delete(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})
    if user and (password == user["password"]):
        users_collection.delete_one({"username": username})
        return JSONResponse(content={"detail": "User deleted successfully"}, status_code=200)
    return JSONResponse(content={"detail": "Invalid username or password"}, status_code=401)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            chat_completion = openai.chat.completions.create(
                model="ft:gpt-3.5-turbo-0125:personal:parachan:9mPXBkOU",
                messages=[{"role": "user", "content": data}],
                max_tokens=150,
                n=1,
                stop=["."],
                temperature=1
            )
            message = chat_completion.choices[0].message.content
            await websocket.send_text(message)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
