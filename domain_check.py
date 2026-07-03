import asyncio
import httpx

RDAP_URL = "https://rdap.verisign.com/com/v1/domain/{}.com"

async def check_one(client: httpx.AsyncClient, name: str) -> dict:
    """Check a single .com via Verisign RDAP.
    200 -> taken, 404 -> available, anything else / errors -> unknown."""
    try:
        resp = await client.get(RDAP_URL.format(name), timeout=5)
    except httpx.RequestError:
        return {"name": name, "status": "unknown"}

    if resp.status_code == 200:
        status = "taken"
    elif resp.status_code == 404:
        status = "available"
    else:
        status = "unknown"
    return {"name": name, "status": status}


async def check_many(names: list[str]) -> list[dict]:
    """Check a batch of names in parallel."""
    async with httpx.AsyncClient() as client:
        tasks = [check_one(client, n) for n in names]
        return await asyncio.gather(*tasks)
