import json
import asyncio

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse, StreamingResponse

from llm.send import (
    generate_async,
    generate_with_skills_async,
    generate_stream,
    generate_with_skills_stream,
    prompt_generate_async,
)
from vector.vector import VectorAI
from vector.web import find_async, get_result
from vector.wiki import wiki_async, get_text, get_link
from core.skillsApi import load_skills, select_relevant_skills

router = APIRouter(prefix="/api")


class SearchTask:
    def __init__(self):
        self.ai = VectorAI()
        self.context = ""
        self.query = ""
        self.skills = []
        self.relevant_skills = []
        self.load_skills()

    def load_skills(self):
        self.skills = load_skills()

    async def search(self, content):
        self.query = content
        self.load_skills()
        self.relevant_skills = select_relevant_skills(content, self.skills)

        async def _vector():
            try:
                return self.ai.ask(content)
            except Exception:
                return ""

        async def _web():
            try:
                await find_async(content)
                return get_result()
            except Exception:
                return ""

        async def _wiki():
            try:
                await wiki_async(content)
                return get_text(), get_link()
            except Exception:
                return "", ""

        vector_r, web_r, wiki_r = await asyncio.gather(
            _vector(), _web(), _wiki(), return_exceptions=False
        )

        wiki_text = wiki_r[0] if isinstance(wiki_r, tuple) else ""
        wiki_link = wiki_r[1] if isinstance(wiki_r, tuple) else ""

        skill_context = ""
        if self.relevant_skills:
            skill_context = "\n\nSKILLS:\n"
            for skill in self.relevant_skills:
                skill_name = skill.get("name", "Unknown")
                skill_content = skill.get("content", "")
                skill_context += f"- {skill_name}: {skill_content}\n"

        self.context = f"""QUESTION:
{content}

AI:
{vector_r}

WEB:
{web_r}

WIKI:
{wiki_text}

LINK:
{wiki_link}
{skill_context}"""
        return self.context

    async def generate_answer(self, reasoning_mode=False):
        if not self.context:
            return "No context"
        try:
            if self.relevant_skills:
                result = await generate_with_skills_async(
                    f"USER: {self.query}\n\nDATA:\n{self.context}",
                    self.relevant_skills,
                    reasoning_mode=reasoning_mode,
                )
            else:
                result = await generate_async(
                    f"USER: {self.query}\n\nDATA:\n{self.context}",
                    reasoning_mode=reasoning_mode,
                )
        except Exception as e:
            return f"Generation error: {e}"
        if not result:
            return "Generation failed"
        return result

    async def generate_answer_stream(self, reasoning_mode=False):
        if not self.context:
            yield "No context"
            return
        try:
            if self.relevant_skills:
                async for chunk in generate_with_skills_stream(
                    f"USER: {self.query}\n\nDATA:\n{self.context}",
                    self.relevant_skills,
                    reasoning_mode=reasoning_mode,
                ):
                    yield chunk.content
            else:
                async for chunk in generate_stream(
                    f"USER: {self.query}\n\nDATA:\n{self.context}",
                    reasoning_mode=reasoning_mode,
                ):
                    yield chunk.content
        except Exception as e:
            yield f"Generation error: {e}"


class SearchResult:
    async def generate_result(self, task, reasoning_mode=False):
        if not task:
            return "No result"
        return await task.generate_answer(reasoning_mode=reasoning_mode)


@router.post("/search")
async def api_search(query: str = Form(...), reasoning: bool = Form(False)):
    try:
        task = SearchTask()
        await task.search(query)
        result = await SearchResult().generate_result(task, reasoning_mode=reasoning)
        if not result:
            result = "No results found"
        return JSONResponse(
            content={"result": result, "skills_used": len(task.relevant_skills)}
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/search/stream")
async def api_search_stream(
    query: str = Form(...),
    reasoning: bool = Form(False),
    improve_prompt: bool = Form(False),
):
    async def event_generator():
        try:
            actual_query = query

            if improve_prompt:
                yield f"data: {json.dumps({'type': 'improving_prompt'})}\n\n"
                try:
                    improved = await prompt_generate_async(query)
                    if improved:
                        yield f"data: {json.dumps({'type': 'improved_prompt', 'original': query, 'improved': improved})}\n\n"
                        actual_query = improved
                except Exception:
                    pass

            yield f"data: {json.dumps({'type': 'searching', 'source': 'vector'})}\n\n"
            yield f"data: {json.dumps({'type': 'searching', 'source': 'web'})}\n\n"
            yield f"data: {json.dumps({'type': 'searching', 'source': 'wikipedia'})}\n\n"

            task = SearchTask()
            await task.search(actual_query)

            skill_count = len(task.relevant_skills)
            web_result = get_result()
            web_count = len(web_result.get("links", []))

            yield f"data: {json.dumps({'type': 'search_done', 'source': 'vector'})}\n\n"
            yield f"data: {json.dumps({'type': 'search_done', 'source': 'web', 'results': web_count})}\n\n"
            yield f"data: {json.dumps({'type': 'search_done', 'source': 'wikipedia'})}\n\n"
            yield f"data: {json.dumps({'type': 'search_done', 'source': 'skills', 'results': skill_count})}\n\n"

            async for chunk in task.generate_answer_stream(reasoning_mode=reasoning):
                if chunk:
                    yield f"data: {json.dumps({'type': 'answer_chunk', 'content': chunk})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/prompt/improve")
async def api_prompt_improve(request: dict):
    query = request.get("query", "").strip()
    if not query:
        return JSONResponse(content={"error": "Empty query"}, status_code=400)
    try:
        result = await prompt_generate_async(query)
        return JSONResponse(content={"original": query, "improved": result or query})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/search/web")
async def api_search_web(request: dict):
    query = request.get("query", "").strip()
    if not query:
        return JSONResponse(content={"error": "Empty query"}, status_code=400)
    try:
        await find_async(query, n=5)
        result = get_result()
        links = result.get("links", [])
        texts = result.get("texts", [])
        cards = []
        for i, (link, text) in enumerate(zip(links, texts)):
            title = ""
            for line in text.split("\n"):
                line = line.strip()
                if line and len(line) > 10:
                    title = line[:120]
                    break
            if not title:
                title = link.split("/")[-1][:100]
            cards.append({
                "url": link,
                "title": title,
                "snippet": text[:500],
            })
        return JSONResponse(content={"results": cards, "query": query})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.get("/health")
async def health():
    return {"status": "ok", "service": "LLM-Wiki", "skills_count": len(load_skills())}


@router.post("/agent")
async def api_agent(request: dict):
    query = request.get("query", "").strip()
    mode = request.get("mode", "build")
    history = request.get("history", [])
    if not query:
        return JSONResponse(content={"error": "Empty query"}, status_code=400)

    try:
        from core.agent import Agent
        agent = Agent(mode=mode)
        result = await agent.run(query, mode=mode, history=history)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/agent/stream")
async def api_agent_stream(request: dict):
    query = request.get("query", "").strip()
    mode = request.get("mode", "build")
    history = request.get("history", [])
    if not query:
        async def empty():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Empty query'})}\n\n"
        return StreamingResponse(empty(), media_type="text/event-stream")

    async def event_generator():
        try:
            from core.agent import Agent
            agent = Agent(mode=mode)
            async for event in agent.run_stream(query, mode=mode, history=history):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
