from schemas import DoneClockRequest
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
async def health():
    """
    健康检查
    """
    return "OK"


@app.get("/done_clock/")
async def done_clock(req: DoneClockRequest):
    """
    完成打卡

    记录完成打卡事项
    """
    return {"message": "Hello World"}
