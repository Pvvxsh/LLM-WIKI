import os
import sys
import asyncio
import webbrowser
import threading
import argparse
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from core.skillsApi import router as skills_router
from core.search import router as search_router
from core.filesApi import router as files_router
from core.shellApi import router as shell_router

for x in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(x, None)

os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="LLM-Wiki")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(skills_router)
app.include_router(search_router)
app.include_router(files_router)
app.include_router(shell_router)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "interface")), name="static")


@app.get("/")
async def index():
    return FileResponse(str(BASE_DIR / "interface" / "index.html"))


@app.get("/health")
async def health():
    from core.skillsApi import load_skills
    return {"status": "ok", "service": "LLM-Wiki", "skills_count": len(load_skills())}


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


def open_webview():
    import webview
    window = webview.create_window(
        "LLM-Wiki",
        "http://127.0.0.1:8000",
        width=1200,
        height=800,
        min_size=(900, 600),
        text_select=True,
    )
    webview.start(debug=False)


def main():
    parser = argparse.ArgumentParser(description="LLM-Wiki — AI Wiki with File Manager")
    parser.add_argument("--web", action="store_true", help="Open in browser instead of desktop window")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    import time
    time.sleep(1.5)

    if args.web:
        webbrowser.open(f"http://127.0.0.1:{args.port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        try:
            open_webview()
        except ImportError:
            print("pywebview not installed. Opening in browser instead...")
            print("Install: pip install pywebview")
            webbrowser.open(f"http://127.0.0.1:{args.port}")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopped.")


if __name__ == "__main__":
    main()
