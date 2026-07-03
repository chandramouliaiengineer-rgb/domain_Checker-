from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from naming_rules import passes_quality_filter, build_variations
from llm import generate_names
from domain_check import check_many

app = FastAPI(title="brandgen")


class GenerateRequest(BaseModel):
    description: str
    desired_name: str | None = None


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(req: GenerateRequest):
    raw = await generate_names(req.description, count=28)

    seen, filtered = set(), []
    for name in raw:
        if name not in seen and passes_quality_filter(name):
            seen.add(name)
            filtered.append(name)
    filtered = filtered[:24]

    desired = None
    if req.desired_name:
        desired = req.desired_name.strip().lower()
        if desired.endswith('.com'):
            desired = desired[:-4]
        if desired and desired not in seen:
            filtered.insert(0, desired)
            seen.add(desired)

    results = await check_many(filtered)

    if desired:
        for r in results:
            if r["name"] == desired:
                r["desired"] = True

    # Available first, then unknown, then taken — desired pick always pinned on top.
    order = {"available": 0, "unknown": 1, "taken": 2}
    results.sort(key=lambda r: (not r.get("desired", False), order.get(r["status"], 3)))
    return {"results": results}


class VariationsRequest(BaseModel):
    name: str


@app.post("/variations")
async def variations(req: VariationsRequest):
    candidates = build_variations(req.name)
    results = await check_many(candidates)
    results = [r for r in results if r["status"] != "taken"]
    order = {"available": 0, "unknown": 1}
    results.sort(key=lambda r: order.get(r["status"], 2))
    return {"base": req.name, "results": results[:8]}
