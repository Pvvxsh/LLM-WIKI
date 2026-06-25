import json
import os
import shutil
import subprocess
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
]


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
                timeout=60,
                encoding="utf-8",
                errors="replace",
                env={**os.environ, "NO_PROXY": "*", "no_proxy": "*"},
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            if len(output) > 4000:
                output = output[:4000] + "\n... [обрезано]"
            return {"stdout": output, "returncode": result.returncode, "cwd": _cwd}
        except subprocess.TimeoutExpired:
            return {"error": "Команда выполнялась слишком долго (60с)"}
        except Exception as e:
            return {"error": str(e)}

    elif name == "read_file":
        path = args.get("path", "")
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            if len(content) > 8000:
                content = content[:8000] + "\n... [обрезано]"
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
                    if len(results) >= 20:
                        break
                    fpath = Path(root) / fname
                    try:
                        text = fpath.read_text(encoding="utf-8", errors="ignore")
                        if query.lower() in text.lower():
                            results.append(str(fpath))
                    except Exception:
                        continue
                if len(results) >= 20:
                    break
            return {"results": results, "count": len(results)}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown tool: {name}"}


class Agent:
    def __init__(self):
        self.client = OpenRouterClient()
        self.max_iterations = 15

    def _build_messages(self, query, context=""):
        system = (
            "Ты — AI агент с полным доступом к компьютеру пользователя (Windows 10).\n"
            "У тебя есть инструменты для работы с файловой системой и терминалом.\n\n"
            "КОГДА ИСПОЛЬЗОВАТЬ ИНСТРУМЕНТЫ:\n"
            "- Пользователь просит создать/прочитать/изменить файл → read_file / write_file\n"
            "- Пользователь просит запустить команду/скрипт/программу → execute_command\n"
            "- Пользователь спрашивает что в папке → list_directory\n"
            "- Нужно найти файлы → search_in_files\n"
            "- Нужно создать папку → create_directory\n\n"
            "КОМАНДЫ POWERSHELL (Windows 10):\n"
            "- Установка пакетов: pip install <package>\n"
            "- Запуск Python: python script.py\n"
            "- Навигация: cd path, dir (ls), Get-ChildItem\n"
            "- Копирование: Copy-Item src dst\n"
            "- Перемещение: Move-Item src dst\n"
            "- Удаление: Remove-Item path\n"
            "- Просмотр системных данных: Get-Process, Get-Service, systeminfo\n"
            "- Git: git status, git add ., git commit -m \"msg\", git push\n"
            "- Скачивание файлов: Invoke-WebRequest -Uri url -OutFile file\n"
            "- Проверка портов: Test-NetConnection host -Port port\n"
            "- Запуск в фоне: Start-Process program\n"
            "- Остановка процесса: Stop-Process -Name name -Force\n\n"
            "ПРАВИЛА:\n"
            "- Всегда выполняй то что просит пользователь, не спрашивай подтверждений\n"
            "- Если нужно создать файл и запустить — сделай оба действия\n"
            "- Показывай результаты выполнения команд пользователю\n"
            "- Отвечай на языке пользователя\n"
            "- Будь конкретным, без воды\n"
        )
        if context:
            system += f"\nКОНТЕКСТ:\n{context}\n"

        messages = [{"role": "system", "content": system}]
        messages.append({"role": "user", "content": query})
        return messages

    def _call_llm(self, messages):
        import httpx
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
                "max_tokens": 4096,
                "temperature": 0.3,
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    async def run(self, query, context=""):
        messages = self._build_messages(query, context)
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
