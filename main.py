from datetime import datetime
from typing import Annotated

import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import motor.motor_asyncio

from utils import create_short_url


app = FastAPI()
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
templates = Jinja2Templates(directory="templates")

db_client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017, username="root", password="example")
app_db = db_client["url_shortener"]
collections = app_db["urls"]


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/")
async def shorten_url(request: Request, long_url: Annotated[str, Form()]):
    url_document = await collections.find_one({"long_url": long_url})

    if url_document is None:
        while True:
            short_url = create_short_url()
            if not await collections.find_one({"short_url": short_url}):
                break

        url_document = {"short_url": short_url,
                        "long_url": long_url,
                        "last_used_date": datetime.utcnow().day,
                        "total_clicks": 0}
        await collections.insert_one(url_document)

    context = url_document
    return templates.TemplateResponse(request=request, name="shortened.html", context=context)


@app.get("/{short_url}")
async def url_redirect(short_url: str):
    url_document = await collections.find_one({"short_url": short_url})
    if url_document is None:
        raise HTTPException(status_code=404, detail="Not found URL or shortened URL is expired")

    await collections.update_one(
        {"_id": url_document["_id"]},
        {
            "$set": {"last_used_date": datetime.utcnow()},
            "$inc": {"total_clicks": 1}
        }
    )

    redirect_url = url_document["long_url"]
    return RedirectResponse(redirect_url)


@app.get("/{short_url}/info")
async def url_show_info(request: Request, short_url: str):
    url_document = await collections.find_one({"short_url": short_url})
    context = url_document
    return templates.TemplateResponse(request=request, name="url_info.html", context=context)


@app.post("/{short_url}/edit")
async def url_edit_info(request: Request, new_short_url: Annotated[str, Form()]):
    url_document = await collections.find_one({"short_url": request.path_params["short_url"]})
    await collections.update_one(
        {"_id": url_document["_id"]},
        {
            "$set": {"short_url": new_short_url},
        }
    )
    url_document = await collections.find_one({"short_url": new_short_url})
    context = url_document
    return templates.TemplateResponse(request=request, name="shortened.html", context=context)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5000, log_level="debug")
