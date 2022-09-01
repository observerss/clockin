import sys
from subprocess import Popen

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import DoneClockRequest, AddUserRequest, AddPlanRequest
from handlers.plan import start_scheduler
from handlers.server import handle_done_clock, handle_add_user, handle_add_plan
from utils import handles_error


app = FastAPI()


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/health")
async def health():
    """
    健康检查
    """
    return "OK"


@app.post("/done_clock/")
@handles_error
def done_clock(req: DoneClockRequest):
    """
    完成打卡

    记录完成打卡事项
    """
    handle_done_clock(req)


app2 = FastAPI()

app2.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app2.post("/add_user/")
@handles_error
def add_user(req: AddUserRequest):
    """添加用户信息"""
    handle_add_user(req)


@app2.post("/add_plan/")
@handles_error
def add_plan(req: AddPlanRequest):
    """添加自动打卡脚本"""
    handle_add_plan(req)


if __name__ == "__main__":
    Popen(
        [
            "uvicorn",
            "server:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--proxy-headers",
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    uvicorn.run(
        app=app2,
        host="0.0.0.0",
        port=8001,
        ssl_keyfile="./assets/key.pem",
        ssl_certfile="./assets/cert.pem",
    )
