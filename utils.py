import os
import json
import aiofiles as aiofiles


async def check_and_create_file():
    if not os.path.exists("urls.json"):
        async with aiofiles.open("urls.json", "w") as f:
            await f.write(json.dumps({}))
