from fastapi import FastAPI, Request
import uvicorn
from config import config_
import asyncio

app = FastAPI()


@app.post("/webhook")
async def openproject_webhook(request: Request):
    body_json: dict = await request.json()
    print(body_json)

    return {"status": "ok"}


async def start_fastapi():
    config = uvicorn.Config(app, host=config_.HOST, port=int(config_.PORT), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(start_fastapi())
