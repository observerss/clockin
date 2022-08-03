from schemas import DoneClockRequest
from fastapi import FastAPI
from handlers.plan import start_scheduler
from handlers.server import handle_done_clock

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
async def done_clock(req: DoneClockRequest):
    """
    完成打卡

    记录完成打卡事项
    """
    handle_done_clock(req)
    return dict(code=0, msg="ok")
