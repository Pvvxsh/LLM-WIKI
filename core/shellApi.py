import os
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/shell")

_cwd = str(Path.home())


@router.get("/cwd")
async def get_cwd():
    return JSONResponse(content={"cwd": _cwd})


@router.post("/cwd")
async def set_cwd(request: dict):
    global _cwd
    path = request.get("path", "")
    if not path or not Path(path).exists():
        return JSONResponse(content={"error": "Path not found"}, status_code=400)
    _cwd = str(Path(path).resolve())
    return JSONResponse(content={"cwd": _cwd})


@router.post("/exec")
async def exec_command(request: dict):
    command = request.get("command", "").strip()
    if not command:
        return JSONResponse(content={"error": "Empty command"}, status_code=400)

    timeout = min(request.get("timeout", 30), 120)

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            cwd=_cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "NO_PROXY": "*", "no_proxy": "*"},
        )
        return JSONResponse(content={
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "cwd": _cwd,
        })
    except subprocess.TimeoutExpired:
        return JSONResponse(content={"error": f"Command timed out ({timeout}s)"}, status_code=408)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/read_file")
async def read_file(request: dict):
    path = request.get("path", "")
    if not path:
        return JSONResponse(content={"error": "Empty path"}, status_code=400)

    target = Path(path).resolve()
    if not target.exists():
        return JSONResponse(content={"error": "File not found"}, status_code=404)
    if target.is_dir():
        return JSONResponse(content={"error": "Is directory"}, status_code=400)

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return JSONResponse(content={"content": content, "path": str(target), "size": target.stat().st_size})
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)


@router.post("/write_file")
async def write_file(request: dict):
    path = request.get("path", "")
    content = request.get("content", "")
    if not path:
        return JSONResponse(content={"error": "Empty path"}, status_code=400)

    target = Path(path).resolve()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return JSONResponse(content={"status": "ok", "path": str(target)})
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)


@router.post("/list_dir")
async def list_dir(request: dict):
    path = request.get("path", _cwd)
    if not path:
        path = _cwd

    target = Path(path).resolve()
    if not target.exists():
        return JSONResponse(content={"error": "Path not found"}, status_code=404)
    if not target.is_dir():
        return JSONResponse(content={"error": "Not a directory"}, status_code=400)

    items = []
    try:
        for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith("."):
                continue
            rel = str(item.relative_to(target)).replace("\\", "/")
            items.append({
                "name": item.name,
                "path": str(item).replace("\\", "/"),
                "type": "dir" if item.is_dir() else "file",
                "size": 0 if item.is_dir() else item.stat().st_size,
            })
    except PermissionError:
        return JSONResponse(content={"error": "Access denied"}, status_code=403)

    return JSONResponse(content={"path": str(target).replace("\\", "/"), "items": items})


@router.post("/mkdir")
async def mkdir(request: dict):
    path = request.get("path", "")
    if not path:
        return JSONResponse(content={"error": "Empty path"}, status_code=400)
    target = Path(path).resolve()
    try:
        target.mkdir(parents=True, exist_ok=True)
        return JSONResponse(content={"status": "ok", "path": str(target)})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/delete")
async def delete(request: dict):
    path = request.get("path", "")
    if not path:
        return JSONResponse(content={"error": "Empty path"}, status_code=400)
    target = Path(path).resolve()
    if not target.exists():
        return JSONResponse(content={"error": "Not found"}, status_code=404)
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/search")
async def search_files(request: dict):
    directory = request.get("path", _cwd)
    query = request.get("query", "").strip()
    if not query:
        return JSONResponse(content={"error": "Empty query"}, status_code=400)

    results = []
    target = Path(directory).resolve()
    if not target.exists():
        return JSONResponse(content={"error": "Path not found"}, status_code=404)

    for root, dirs, files in os.walk(target):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if len(results) >= 30:
                break
            fpath = Path(root) / fname
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                if query.lower() in text.lower():
                    results.append({"path": str(fpath).replace("\\", "/"), "name": fpath.name})
            except Exception:
                continue
        if len(results) >= 30:
            break

    return JSONResponse(content={"results": results})
