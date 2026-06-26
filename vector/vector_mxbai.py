from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
import httpx
import os


class VectorMxBai:

    def __init__(self):
        self.embedder = TextEmbedding(model_name="mixedbread-ai/mxbai-embed-large-v1")
        self.qdrant = QdrantClient(":memory:")
        self.api_key = os.getenv("API", "")

        docs = [
            "Python — высокоуровневый язык программирования общего назначения.",
            "JavaScript — язык программирования для веб-приложений.",
            "TypeScript — строго типизированный язык программирования.",
            "Node.js — среда выполнения JavaScript на сервере.",
            "FastAPI — современный фреймворк для создания API на Python.",
            "React — библиотека для построения пользовательских интерфейсов.",
            "Vue.js — прогрессивный фреймворк для создания UI.",
            "PostgreSQL — мощная реляционная база данных.",
            "Redis — хранилище данных в памяти.",
            "Nginx — веб-сервис и обратный прокси.",
        ]

        vectors = list(self.embedder.embed(docs))

        self.qdrant.create_collection(
            collection_name="mxbai",
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )

        self.qdrant.upsert(
            collection_name="mxbai",
            points=[
                PointStruct(id=i, vector=vectors[i], payload={"text": docs[i]})
                for i in range(len(docs))
            ],
        )

    def ask(self, question):
        vector = list(self.embedder.embed([question]))[0]

        result = self.qdrant.query_points(
            collection_name="mxbai", query=vector, limit=3
        )

        context = "\n".join(x.payload["text"] for x in result.points)

        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/owl-alpha",
                "max_tokens": 512,
                "messages": [
                    {"role": "system", "content": "Answer only using context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
                ],
            },
            timeout=15,
        )

        return resp.json()["choices"][0]["message"]["content"]
