import os
from dotenv import load_dotenv
from clients.openrouter import OpenRouterClient

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

_client = OpenRouterClient()
nocode = os.getenv("NO_CODE", "")
reasoning = os.getenv("REASONING", "")
prompt_env = os.getenv("PROMPT_GENERATE", "")
query_p = os.getenv("QUERY", "")
entity = os.getenv("ENTITY", "")


def format_skill(skill):
    name = str(skill.get("name", "Unknown skill"))
    description = str(skill.get("description", "")).strip()
    tags = skill.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    content = str(skill.get("content", "")).strip()
    if len(content) > 2500:
        content = content[:2500]
    parts = [f"Skill: {name}"]
    if description:
        parts.append(f"Description: {description}")
    if tags:
        parts.append(f"Tags: {', '.join(str(x) for x in tags)}")
    if content:
        parts.append(f"Content:\n{content}")
    return "\n".join(parts)


def _system_msg(sys_msg):
    return (
        f"{sys_msg}\n\n"
        "Ты работаешь на Windows 10. Пользователь может попросить тебя выполнить действия.\n"
        "Когда нужно что-то сделать — отвечай с конкретными командами PowerShell.\n\n"
        "Формат ответа:\n"
        "- Краткий прямой ответ в начале\n"
        "- Команды/код если нужно выполнить действие\n"
        "- Объяснение что делает каждая команда\n"
        "- Примеры использования\n\n"
        "PowerShell команды:\n"
        "- pip install package — установка пакетов Python\n"
        "- python script.py — запуск Python\n"
        "- Get-ChildItem — список файлов (аналог ls)\n"
        "- Get-Content file — чтение файла\n"
        "- Set-Content file — запись в файл\n"
        "- New-Item -ItemType Directory — создание папки\n"
        "- Remove-Item — удаление\n"
        "- Copy-Item / Move-Item — копирование/перемещение\n"
        "- Get-Process — список процессов\n"
        "- systeminfo — информация о системе\n"
        "- git add . && git commit -m \"msg\" — коммит\n"
        "- Invoke-WebRequest -Uri url -OutFile file — скачивание\n\n"
        "Правила:\n"
        "- Без воды — каждое предложение полезно\n"
        "- Markdown: заголовки, таблицы, списки, код\n"
        "- Отвечай на языке пользователя\n"
        "- Не спрашивай уточнений — давай лучший ответ"
    )


async def generate_async(content: str, reasoning_mode: bool = False) -> str:
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": content},
    ]
    return await _client.complete(messages, max_tokens=2048, temperature=0.7)


async def generate_with_skills_async(content: str, skills: list, reasoning_mode: bool = False) -> str:
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    skill_context = "\n\n".join(format_skill(s) for s in skills[:3]) if skills else ""
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Релевантные навыки:\n{skill_context}\n\nВопрос:\n{content}"},
    ]
    return await _client.complete(messages, max_tokens=2048, temperature=0.7)


async def generate_stream(content: str, reasoning_mode: bool = False):
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": content},
    ]
    async for chunk in _client.stream(messages, max_tokens=2048, temperature=0.7):
        yield chunk


async def generate_with_skills_stream(content: str, skills: list, reasoning_mode: bool = False):
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    skill_context = "\n\n".join(format_skill(s) for s in skills[:3]) if skills else ""
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Релевантные навыки:\n{skill_context}\n\nВопрос:\n{content}"},
    ]
    async for chunk in _client.stream(messages, max_tokens=2048, temperature=0.7):
        yield chunk


async def prompt_generate_async(content: str) -> str:
    messages = [
        {"role": "system", "content": query_p},
        {"role": "system", "content": entity},
        {"role": "system", "content": prompt_env},
        {"role": "user", "content": content},
    ]
    return await _client.complete(messages, max_tokens=512, temperature=0.5)


def generate(content: str, reasoning_mode: bool = False):
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    return _client.complete_sync(
        [{"role": "system", "content": sys_msg}, {"role": "user", "content": content}],
        max_tokens=2048,
        temperature=0.7,
    )


def generate_with_skills(content: str, skills: list, reasoning_mode: bool = False):
    sys_msg = _system_msg(reasoning if reasoning_mode else nocode)
    skill_context = "\n\n".join(format_skill(s) for s in skills[:3]) if skills else ""
    messages = [
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Релевантные навыки:\n{skill_context}\n\nВопрос:\n{content}"},
    ]
    return _client.complete_sync(messages, max_tokens=2048, temperature=0.7)


def prompt_generate(content: str):
    messages = [
        {"role": "system", "content": query_p},
        {"role": "system", "content": entity},
        {"role": "system", "content": prompt_env},
        {"role": "user", "content": content},
    ]
    return _client.complete_sync(messages, max_tokens=512, temperature=0.5)
