import os

from fastapi import FastAPI

import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(app, host=host, port=port)