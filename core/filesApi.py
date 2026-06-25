import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent.parent

router = APIRouter(prefix="/api/files")


def safe_path(p):
    p = str(p or "").replace("\\", "/").strip("/")
    full = (BASE_DIR / p).resolve()
    if not str(full).startswith(str(BASE_DIR.resolve())):
        return None
    return full


def file_info(path, base):
    rel = path.relative_to(base)
    is_dir = path.is_dir()
    return {
        "name": path.name,
        "path": str(rel).replace("\\", "/"),
        "type": "dir" if is_dir else "file",
        "size": 0 if is_dir else path.stat().st_size,
        "ext": "" if is_dir else path.suffix.lower(),
    }


@router.get("/tree")
async def file_tree(path: str = Query("", alias="path")):
    target = safe_path(path)
    if not target or not target.exists():
        return JSONResponse(content={"error": "Path not found"}, status_code=404)
    if not target.is_dir():
        return JSONResponse(content={"error": "Not a directory"}, status_code=400)

    items = []
    try:
        for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            items.append(file_info(item, BASE_DIR))
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"path": str(target.relative_to(BASE_DIR)).replace("\\", "/"), "items": items})


@router.get("/read")
async def file_read(path: str = Query(..., alias="path")):
    target = safe_path(path)
    if not target or not target.exists():
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    if target.is_dir():
        return JSONResponse(content={"error": "Cannot read directory"}, status_code=400)

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={
        "path": str(target.relative_to(BASE_DIR)).replace("\\", "/"),
        "content": content,
        "size": target.stat().st_size,
        "ext": target.suffix.lower(),
    })


@router.post("/write")
async def file_write(request: dict):
    path = request.get("path", "")
    content = request.get("content", "")
    target = safe_path(path)
    if not target:
        return JSONResponse(content={"error": "Invalid path"}, status_code=400)

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"status": "ok", "path": str(target.relative_to(BASE_DIR)).replace("\\", "/")})


@router.post("/mkdir")
async def file_mkdir(request: dict):
    path = request.get("path", "")
    target = safe_path(path)
    if not target:
        return JSONResponse(content={"error": "Invalid path"}, status_code=400)
    if target.exists():
        return JSONResponse(content={"error": "Already exists"}, status_code=400)

    try:
        target.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"status": "ok", "path": str(target.relative_to(BASE_DIR)).replace("\\", "/")})


@router.delete("/delete")
async def file_delete(request: dict):
    path = request.get("path", "")
    target = safe_path(path)
    if not target or not target.exists():
        return JSONResponse(content={"error": "Not found"}, status_code=404)
    if str(target) == str(BASE_DIR):
        return JSONResponse(content={"error": "Cannot delete root"}, status_code=400)

    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"status": "ok"})


@router.post("/rename")
async def file_rename(request: dict):
    old_path = request.get("old_path", "")
    new_name = request.get("new_name", "")
    if not new_name or "/" in new_name or "\\" in new_name:
        return JSONResponse(content={"error": "Invalid name"}, status_code=400)

    target = safe_path(old_path)
    if not target or not target.exists():
        return JSONResponse(content={"error": "Not found"}, status_code=404)

    new_target = target.parent / new_name
    if new_target.exists():
        return JSONResponse(content={"error": "Name already taken"}, status_code=400)

    try:
        target.rename(new_target)
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"status": "ok", "path": str(new_target.relative_to(BASE_DIR)).replace("\\", "/")})


@router.post("/search")
async def file_search(request: dict):
    query = request.get("query", "").strip()
    if not query:
        return JSONResponse(content={"error": "Empty query"}, status_code=400)

    results = []
    max_results = 50

    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
        for fname in files:
            if len(results) >= max_results:
                break
            fpath = Path(root) / fname
            if fpath.suffix.lower() not in (".py", ".md", ".txt", ".json", ".js", ".css", ".html", ".bat", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env"):
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if query.lower() in text.lower():
                    rel = str(fpath.relative_to(BASE_DIR)).replace("\\", "/")
                    lines = text.splitlines()
                    match_lines = []
                    for i, line in enumerate(lines, 1):
                        if query.lower() in line.lower():
                            match_lines.append({"line": i, "text": line.strip()[:200]})
                            if len(match_lines) >= 3:
                                break
                    results.append({"path": rel, "name": fpath.name, "matches": match_lines})
            except Exception:
                continue
        if len(results) >= max_results:
            break

    return JSONResponse(content={"results": results, "total": len(results)})
