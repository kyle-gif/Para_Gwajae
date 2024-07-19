from fastapi import FastAPI, Request, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from starlette.responses import JSONResponse
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv


app = FastAPI()
app.mount("/static", StaticFiles(directory="/home/fallenegg/CLionProjects/Para_Gwajae/app/static"), name="static")
load_dotenv()

# MongoDB 클라이언트 설정
openaiClient = OpenAI()
client = MongoClient("mongodb://localhost:27017")
db = client.login_db
users_collection = db.users

# HTML 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 세션 데이터 저장
sessions = {}  # 메모리 내 세션 저장소 (단순 예시용)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # return templates.TemplateResponse("index.html", {"request": request})
    html_content = Path("templates/index.html").read_text()
    return HTMLResponse(content=html_content)


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="사용자 이름과 비밀번호를 모두 입력하세요.")
    users_collection.insert_one({"username": username, "password": password})
    return RedirectResponse(url="/", status_code=303)


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if not username or not password:
        raise HTTPException(status_code=400, detail="사용자 이름과 비밀번호를 모두 입력하세요.")
    user = users_collection.find_one({"username": username})
    if user and (password == user["password"]):
        session_id = str(hash(username))  # 세션 ID 생성 (간단한 예시)
        sessions[session_id] = username
        response = JSONResponse(content={"detail": "로그인 성공"}, status_code=200)
        response.set_cookie(key="session_id", value=session_id)
        return response
    return JSONResponse(content={"detail": "잘못된 자격 증명"}, status_code=401)


@app.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]  # 세션 삭제
    response = RedirectResponse(url="/")
    response.delete_cookie(key="session_id")
    return response


@app.post("/delete")
async def delete(request: Request, username: str = Form(...), password: str = Form(...)):
    user = users_collection.find_one({"username": username})
    if user and (password == user["password"]):
        users_collection.delete_one({"username": username})
        return JSONResponse(content={"detail": "사용자 삭제 성공"}, status_code=200)
    return JSONResponse(content={"detail": "잘못된 사용자 이름 또는 비밀번호"}, status_code=401)


@app.get("/check-session")
async def check_session(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        return JSONResponse(content={"detail": "사용자가 로그인되어 있습니다."}, status_code=200)
    return JSONResponse(content={"detail": "사용자가 로그인되어 있지 않습니다."}, status_code=401)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = websocket.headers.get("cookie", "").split("session_id=")[-1]
    if session_id not in sessions:
        await websocket.close(code=4000)  # 인증되지 않은 접근에 대한 사용자 정의 코드로 연결 종료
        return
    try:
        while True:
            data = await websocket.receive_text()
            # 여기에 ChatGPT API 호출 코드 추가
            chat_completion = openaiClient.chat.completions.create(
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
