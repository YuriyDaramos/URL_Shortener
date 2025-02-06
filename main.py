import os
import random
import string
import json
from typing import Annotated

import aiofiles as aiofiles
import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static", html=True), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/")
async def shorten_url(request: Request, long_url: Annotated[str, Form()]):
    await check_and_create_file()

    async with aiofiles.open("urls.json", "r") as f:
        file_content = await f.read()
        if not file_content:
            existing_data = {}
        else:
            existing_data = json.loads(file_content)

    shortened_url = None

    for existing_short_url, existing_long_url in existing_data.items():
        if existing_long_url == long_url:
            shortened_url = existing_short_url
            break

    if not shortened_url:
        while True:
            shortened_url = "".join([random.choice(string.ascii_letters + string.digits) for _ in range(5)])
            if shortened_url not in existing_data:
                break
        existing_data[shortened_url] = long_url
        async with aiofiles.open("urls.json", "w") as f:
            await f.write(json.dumps(existing_data))

    context = {"short_url": shortened_url,
               "long_url": long_url}
    return templates.TemplateResponse(request=request, name="shortened.html", context=context)


@app.get("/{shortened_url}")
async def url_redirect(shortened_url: str):
    await check_and_create_file()

    async with aiofiles.open("urls.json", "r") as f:
        existing_data = json.loads(await f.read())
        if shortened_url not in existing_data:
            raise HTTPException(status_code=404, detail="Not found URL or shortened URL is expired")

    redirect_url = existing_data[shortened_url]
    return RedirectResponse(redirect_url)


async def check_and_create_file():
    if not os.path.exists("urls.json"):
        async with aiofiles.open("urls.json", "w") as f:
            await f.write(json.dumps({}))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="info")
