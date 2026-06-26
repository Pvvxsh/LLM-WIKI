import json
import os
import shutil
import subprocess
import asyncio
import httpx
from pathlib import Path

from clients.openrouter import OpenRouterClient

_cwd = str(Path.home())

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Выполнить команду PowerShell на компьютере пользователя. Возвращает stdout, stderr и код возврата. Используй для запуска скриптов, установки пакетов, проверки системы и любых операций в терминале.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Команда PowerShell для выполнения"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Прочитать содержимое файла с диска. Возвращает текст файла.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Полный путь к файлу"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Записать текст в файл. Создаёт файл если нет, перезаписывает если есть. Создаёт родительские папки автоматически.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Полный путь к файлу"
                    },
                    "content": {
                        "type": "string",
                        "description": "Содержимое для записи"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Показать список файлов и папок в директории.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к папке (пусто = текущая)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_directory",
            "description": "Создать папку (и родительские если нужно).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к новой папке"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Удалить файл или папку. Необратимо!",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу или папке"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "Поиск по содержимому файлов в указанной директории. Возвращает пути файлов где найдено совпадение.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Директория для поиска"
                    },
                    "query": {
                        "type": "string",
                        "description": "Строка для поиска"
                    }
                },
                "required": ["directory", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Поиск в интернете. Возвращает текстовые результаты из Google, DuckDuckGo и Bing. Используй для актуальной информации, документации, новостей.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_skills",
            "description": "Поиск доступных скиллов (навыков) в базе LLM-Wiki. Возвращает список найденных скиллов с именами и описаниями.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ключевые слова для поиска скиллов"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "install_skill",
            "description": "Установить скилл (навык) из базы LLM-Wiki. После установки скилл доступен для использования. Пользователь может сказать 'установи скилл X'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Имя или slug скилла для установки"
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Выполнить Python-скрипт. Возвращает stdout, stderr и код возврата.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python-код для выполнения"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_command",
            "description": "Выполнить git-команду в указанной директории.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Git команда (без 'git')"
                    },
                    "directory": {
                        "type": "string",
                        "description": "Рабочая директория (пусто = текущая)"
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "http_request",
            "description": "Выполнить HTTP-запрос к API или веб-странице. Возвращает статус, заголовки и тело ответа.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL для запроса"
                    },
                    "method": {
                        "type": "string",
                        "description": "HTTP метод (GET, POST, PUT, DELETE)",
                        "enum": ["GET", "POST", "PUT", "DELETE"]
                    },
                    "body": {
                        "type": "string",
                        "description": "Тело запроса (для POST/PUT)"
                    },
                    "headers": {
                        "type": "object",
                        "description": "Заголовки запроса"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_github_skills",
            "description": "Скачать скиллы (навыки) из GitHub репозитория. Скачивает все .md файлы и сохраняет как скиллы. Формат: owner/repo или полный URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo": {
                        "type": "string",
                        "description": "GitHub репозиторий: owner/repo или https://github.com/owner/repo"
                    },
                    "path": {
                        "type": "string",
                        "description": "Путь в репозитории к папке со скиллами (пусто = корень)"
                    }
                },
                "required": ["repo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "Показать список доступных скиллов или их категорий. Помогает понять какие скиллы уже установлены.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Фильтр по категории (пусто = все)"
                    },
                    "limit": {
                        "type": "number",
                        "description": "Максимум скиллов (по умолчанию 20)"
                    }
                }
            }
        }
    },
]


_skills_cache = None
_skills_summary_cache = None


def _load_skills_data():
    global _skills_cache
    if _skills_cache is not None:
        return _skills_cache
    try:
        skills_file = Path(__file__).resolve().parent.parent / "skills.json"
        data = json.loads(skills_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            _skills_cache = [x for x in data if isinstance(x, dict)]
            return _skills_cache
    except Exception:
        pass
    return []


def _get_skills_summary():
    global _skills_summary_cache
    if _skills_summary_cache:
        return _skills_summary_cache
    skills = _load_skills_data()
    lines = []
    for s in skills[:300]:
        name = s.get("name", "")
        desc = (s.get("description") or "")[:80]
        if name:
            lines.append(f"- {name}: {desc}")
    _skills_summary_cache = "\n".join(lines) if lines else "(нет скиллов)"
    return _skills_summary_cache


def execute_tool(name, args):
    global _cwd

    if name == "execute_command":
        command = args.get("command", "")
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                cwd=_cwd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "NO_PROXY": "*", "no_proxy": "*"},
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            if len(output) > 20000:
                output = output[:20000] + "\n... [обрезано]"
            return {"stdout": output, "returncode": result.returncode, "cwd": _cwd}
        except subprocess.TimeoutExpired:
            return {"error": "Команда выполнялась слишком долго (300с)"}
        except Exception as e:
            return {"error": str(e)}

    elif name == "read_file":
        path = args.get("path", "")
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            if len(content) > 50000:
                content = content[:50000] + "\n... [обрезано]"
            return {"content": content, "path": path}
        except Exception as e:
            return {"error": str(e)}

    elif name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return {"status": "ok", "path": str(p)}
        except Exception as e:
            return {"error": str(e)}

    elif name == "list_directory":
        path = args.get("path", _cwd)
        if not path:
            path = _cwd
        try:
            target = Path(path)
            if not target.exists():
                return {"error": "Папка не найдена"}
            items = []
            for item in sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.name.startswith("."):
                    continue
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": 0 if item.is_dir() else item.stat().st_size,
                })
            return {"path": str(target), "items": items}
        except Exception as e:
            return {"error": str(e)}

    elif name == "create_directory":
        path = args.get("path", "")
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return {"status": "ok", "path": path}
        except Exception as e:
            return {"error": str(e)}

    elif name == "delete_file":
        path = args.get("path", "")
        try:
            target = Path(path)
            if not target.exists():
                return {"error": "Не найдено"}
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            return {"status": "deleted", "path": path}
        except Exception as e:
            return {"error": str(e)}

    elif name == "search_in_files":
        directory = args.get("directory", _cwd)
        query = args.get("query", "")
        results = []
        try:
            for root, dirs, files in os.walk(Path(directory)):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if len(results) >= 200:
                        break
                    fpath = Path(root) / fname
                    try:
                        text = fpath.read_text(encoding="utf-8", errors="ignore")
                        if query.lower() in text.lower():
                            results.append(str(fpath))
                    except Exception:
                        continue
                if len(results) >= 200:
                    break
            return {"results": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e)}

    elif name == "web_search":
        query = args.get("query", "")
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from vector.web import find_async, get_result
            loop = asyncio.new_event_loop()
            loop.run_until_complete(find_async(query, n=3))
            result = get_result()
            texts = result.get("texts", [])
            links = result.get("links", [])
            combined = []
            for i, (link, text) in enumerate(zip(links, texts)):
                combined.append(f"[{i+1}] {link}\n{text[:1500]}")
            return {"results": combined, "count": len(combined)}
        except Exception as e:
            return {"error": str(e)}

    elif name == "search_skills":
        query = args.get("query", "")
        try:
            skills = _load_skills_data()
            query_lower = query.lower()
            matches = []
            for s in skills:
                name = s.get("name", "")
                desc = s.get("description", "")
                tags = s.get("tags", [])
                if isinstance(tags, list):
                    tags_str = " ".join(str(t) for t in tags)
                else:
                    tags_str = ""
                text = f"{name} {desc} {tags_str}".lower()
                if any(word in text for word in query_lower.split()):
                    matches.append({
                        "name": name,
                        "description": desc[:200],
                        "tags": tags if isinstance(tags, list) else [],
                    })
            return {"skills": matches[:10], "total": len(skills)}
        except Exception as e:
            return {"error": str(e)}

    elif name == "install_skill":
        skill_name = args.get("skill_name", "")
        try:
            skills = _load_skills_data()
            slug = skill_name.lower().replace(" ", "-").replace("_", "-")
            found = None
            for s in skills:
                s_name = s.get("name", "").lower().replace(" ", "-").replace("_", "-")
                s_filename = Path(s.get("filename", "")).stem.lower()
                if slug in s_name or slug in s_filename or s_name in slug:
                    found = s
                    break
            if not found:
                for s in skills:
                    s_name = s.get("name", "").lower()
                    if any(word in s_name for word in slug.split("-")):
                        found = s
                        break
            if not found:
                return {"error": f"Скилл '{skill_name}' не найден. Используй search_skills для поиска."}
            filename = found.get("filename", "")
            if filename:
                skill_path = Path(__file__).resolve().parent.parent / "skills" / filename
                if skill_path.exists():
                    content = skill_path.read_text(encoding="utf-8", errors="replace")
                    return {
                        "status": "installed",
                        "name": found.get("name", ""),
                        "description": found.get("description", ""),
                        "content": content[:5000],
                    }
            return {
                "status": "installed",
                "name": found.get("name", ""),
                "description": found.get("description", ""),
                "content": found.get("content", "")[:5000],
            }
        except Exception as e:
            return {"error": str(e)}

    elif name == "run_python":
        code = args.get("code", "")
        try:
            result = subprocess.run(
                ["python", "-c", code],
                cwd=_cwd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            if len(output) > 20000:
                output = output[:20000] + "\n... [обрезано]"
            return {"stdout": output, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": "Скрипт выполнялся слишком долго (120с)"}
        except Exception as e:
            return {"error": str(e)}

    elif name == "git_command":
        command = args.get("command", "")
        directory = args.get("directory", _cwd)
        try:
            result = subprocess.run(
                ["git"] + command.split(),
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            return {"stdout": output, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"error": "Git-команда выполнялась слишком долго"}
        except Exception as e:
            return {"error": str(e)}

    elif name == "http_request":
        url = args.get("url", "")
        method = args.get("method", "GET").upper()
        body = args.get("body", "")
        headers = args.get("headers", {})
        try:
            with httpx.Client(timeout=30) as client:
                kwargs = {"url": url, "headers": headers}
                if body and method in ("POST", "PUT"):
                    kwargs["content"] = body
                resp = getattr(client, method.lower())(**kwargs)
                text = resp.text
                if len(text) > 20000:
                    text = text[:20000] + "\n... [обрезано]"
                return {"status": resp.status_code, "body": text, "headers": dict(resp.headers)}
        except Exception as e:
            return {"error": str(e)}

    elif name == "download_github_skills":
        repo = args.get("repo", "")
        path = args.get("path", "")
        try:
            import re as _re
            match = _re.search(r"github\.com/([^/]+)/([^/]+)", repo)
            if match:
                owner, repo_name = match.group(1), match.group(2)
            else:
                parts = repo.strip("/").split("/")
                if len(parts) >= 2:
                    owner, repo_name = parts[0], parts[1]
                else:
                    return {"error": "Неверный формат. Используй owner/repo или URL"}

            api_url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}".rstrip("/")
            resp = httpx.get(api_url, timeout=30, follow_redirects=True)
            if resp.status_code != 200:
                return {"error": f"GitHub API вернул {resp.status_code}: {resp.text[:500]}"}

            items = resp.json()
            if not isinstance(items, list):
                items = [items]

            md_files = []
            for item in items:
                if item.get("type") == "file" and item.get("name", "").endswith(".md"):
                    download_url = item.get("download_url")
                    if download_url:
                        file_resp = httpx.get(download_url, timeout=30)
                        if file_resp.status_code == 200:
                            content = file_resp.text
                            name = item["name"].replace(".md", "").replace("-", " ").replace("_", " ").title()
                            md_files.append({"name": name, "content": content, "filename": item["name"]})

            if not md_files:
                return {"error": "Не найдено .md файлов в репозитории", "repo": f"{owner}/{repo_name}"}

            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from core.skillsApi import save_skill_payload

            saved = []
            for f in md_files:
                skill, err = save_skill_payload(
                    {"name": f["name"], "content": f["content"]},
                    source=f"github:{owner}/{repo_name}",
                    filename=f["filename"],
                )
                if not err:
                    saved.append(f["name"])

            return {
                "status": "ok",
                "repo": f"{owner}/{repo_name}",
                "total_found": len(md_files),
                "installed": len(saved),
                "skills": saved,
            }
        except Exception as e:
            return {"error": str(e)}

    elif name == "list_skills":
        category = args.get("category", "")
        limit = int(args.get("limit", 20))
        try:
            skills = _load_skills_data()
            if category:
                cat_lower = category.lower()
                skills = [s for s in skills if cat_lower in s.get("name", "").lower()
                          or cat_lower in s.get("description", "").lower()
                          or any(cat_lower in str(t).lower() for t in (s.get("tags") or []))]

            result = []
            for s in skills[:limit]:
                result.append({
                    "name": s.get("name", ""),
                    "description": (s.get("description") or "")[:150],
                    "tags": s.get("tags", []),
                    "source": s.get("source", ""),
                })
            return {"skills": result, "total": len(skills), "showing": len(result)}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown tool: {name}"}


class Agent:
    def __init__(self, mode="build"):
        self.client = OpenRouterClient()
        self.max_iterations = 999
        self.mode = mode

    def _build_messages(self, query, context="", mode="build", history=None):
        skills_summary = _get_skills_summary()

        if mode == "plan":
            system = (
                "Ты — AI агент LLM-WIKI в режиме PLAN (планирование).\n"
                "Твоя задача — проанализировать запрос, задать вопросы пользователю и составить план.\n\n"
                "ПРАВИЛА:\n"
                "1. Проанализируй запрос пользователя\n"
                "2. Задай 2-4 уточняющих вопроса (просто напиши их текстом)\n"
                "3. После получения ответов — составь подробный план\n"
                "4. В конце плана напиши: Готов к реализации? (Да/Нет)\n"
                "5. Не выполняй действия — только планируй\n"
                "6. Помни весь предыдущий контекст разговора\n\n"
                f"ДОСТУПНЫЕ СКИЛЛЫ:\n{skills_summary}\n"
            )
        elif mode == "compose":
            system = (
                "Ты — AI агент LLM-WIKI в режиме COMPOSE (создание контента).\n"
                "Создавай качественный контент: статьи, код, документацию, скрипты.\n\n"
                "ПРАВИЛА:\n"
                "- Создавай готовый, рабочий контент\n"
                "- Используй markdown форматирование\n"
                "- Код должен быть готов к использованию\n"
                "- Давай полные решения, не частичные\n"
                "- Отвечай на языке пользователя\n"
                "- Помни весь предыдущий контекст разговора\n\n"
                f"ДОСТУПНЫЕ СКИЛЛЫ:\n{skills_summary}\n"
            )
        else:
            system = (
                "Ты — AI агент LLM-WIKI в режиме BUILD (полный доступ к компьютеру).\n"
                "У тебя есть полный доступ к файловой системе, терминалу, интернету и скиллам.\n\n"
                "У ТЕБЯ ЕСТЬ ИНСТРУМЕНТЫ:\n"
                "- execute_command — выполнение PowerShell команд\n"
                "- read_file / write_file — работа с файлами\n"
                "- list_directory / create_directory / delete_file — файловая система\n"
                "- search_in_files — поиск в файлах\n"
                "- web_search — поиск в интернете\n"
                "- search_skills / install_skill / list_skills — работа со скиллами\n"
                "- download_github_skills — скачать скиллы из GitHub\n"
                "- run_python — выполнение Python-кода\n"
                "- git_command — git операции\n"
                "- http_request — HTTP запросы к API\n\n"
                "ВЕБ-РАЗРАБОТКА:\n"
                "- Создавай HTML/CSS/JS файлы для сайтов\n"
                "- Используй современный CSS (Flexbox, Grid, переменные)\n"
                "- Делай адаптивный дизайн (mobile-first)\n"
                "- Создавай файлы: index.html, styles.css, script.js\n"
                "- Для запуска: python -m http.server 8080\n\n"
                "ПРАВИЛА:\n"
                "- ВСЕГДА выполняй то что просит пользователь\n"
                "- Помни весь предыдущий контекст разговора\n"
                "- Показывай результаты выполнения команд\n"
                "- Отвечай на языке пользователя\n"
                "- Будь конкретным, без воды\n\n"
                f"ДОСТУПНЫЕ СКИЛЛЫ:\n{skills_summary}\n"
            )
            if context:
                system += f"\nКОНТЕКСТ:\n{context}\n"

        messages = [{"role": "system", "content": system}]
        if history:
            messages.extend(history[-20:])
        messages.append({"role": "user", "content": query})
        return messages

    def _call_llm(self, messages):
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.client.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.client.model,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "max_tokens": 16384,
                "temperature": 0.3,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    async def _call_llm_stream(self, messages):
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.client.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.client.model,
                    "messages": messages,
                    "tools": TOOLS,
                    "tool_choice": "auto",
                    "max_tokens": 16384,
                    "temperature": 0.3,
                    "stream": True,
                },
            ) as resp:
                resp.raise_for_status()
                collected_content = ""
                collected_tool_calls = {}
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:]
                    if payload.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                        choice = chunk["choices"][0]
                        delta = choice.get("delta", {})
                        content = delta.get("content", "")
                        finish = choice.get("finish_reason")

                        if content:
                            collected_content += content
                            yield {"type": "answer_chunk", "content": content}

                        if delta.get("tool_calls"):
                            for tc in delta["tool_calls"]:
                                idx = tc.get("index", 0)
                                if idx not in collected_tool_calls:
                                    collected_tool_calls[idx] = {
                                        "id": tc.get("id", ""),
                                        "function": {"name": "", "arguments": ""}
                                    }
                                if tc.get("id"):
                                    collected_tool_calls[idx]["id"] = tc["id"]
                                func = tc.get("function", {})
                                if func.get("name"):
                                    collected_tool_calls[idx]["function"]["name"] = func["name"]
                                if func.get("arguments"):
                                    collected_tool_calls[idx]["function"]["arguments"] += func["arguments"]

                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

                if collected_tool_calls:
                    yield {"type": "tool_calls", "calls": list(collected_tool_calls.values())}
                else:
                    yield {"type": "done", "content": collected_content}

    async def run_stream(self, query, context="", mode="build", history=None):
        messages = self._build_messages(query, context, mode, history)

        for i in range(self.max_iterations):
            try:
                collected = {"tool_calls": [], "done": False, "content": ""}
                async for event in self._call_llm_stream(messages):
                    if event["type"] == "answer_chunk":
                        collected["content"] += event["content"]
                    elif event["type"] == "tool_calls":
                        collected["tool_calls"] = event["calls"]
                    elif event["type"] == "done":
                        if not collected["tool_calls"]:
                            yield {"type": "answer_chunk", "content": collected["content"]}
                            yield {"type": "done"}
                            return

                if collected["tool_calls"]:
                    if collected["content"]:
                        yield {"type": "thinking", "content": collected["content"]}

                    assistant_msg = {"role": "assistant", "content": collected["content"] or None, "tool_calls": collected["tool_calls"]}
                    messages.append(assistant_msg)

                    for tc in collected["tool_calls"]:
                        func_name = tc["function"]["name"]
                        try:
                            func_args = json.loads(tc["function"]["arguments"])
                        except json.JSONDecodeError:
                            func_args = {}

                        yield {"type": "action_start", "tool": func_name, "args": func_args}

                        result = execute_tool(func_name, func_args)

                        yield {"type": "action_result", "tool": func_name, "args": func_args, "result": result}

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": json.dumps(result, ensure_ascii=False),
                        })
                else:
                    if collected["content"]:
                        yield {"type": "answer_chunk", "content": collected["content"]}
                    yield {"type": "done"}
                    return

            except Exception as e:
                yield {"type": "error", "content": f"Ошибка: {e}"}
                yield {"type": "done"}
                return

        yield {"type": "answer_chunk", "content": "Достигнут лимит итераций агента"}
        yield {"type": "done"}

    async def run(self, query, context="", mode="build", history=None):
        messages = self._build_messages(query, context, mode, history)
        actions = []

        for i in range(self.max_iterations):
            try:
                response = self._call_llm(messages)
            except Exception as e:
                return {"answer": f"Ошибка LLM: {e}", "actions": actions}

            choice = response["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason", "")

            if message.get("tool_calls"):
                tool_calls = message["tool_calls"]
                messages.append(message)

                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    try:
                        func_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        func_args = {}

                    result = execute_tool(func_name, func_args)
                    actions.append({
                        "tool": func_name,
                        "args": func_args,
                        "result": result,
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, ensure_ascii=False),
                    })
            else:
                content = message.get("content", "")
                return {"answer": content, "actions": actions}

        return {"answer": "Достигнут лимит итераций агента", "actions": actions}
