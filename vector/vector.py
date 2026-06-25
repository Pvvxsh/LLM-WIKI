from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
import httpx
import os


class VectorAI:

    def __init__(self):
        self.embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        self.qdrant = QdrantClient(":memory:")
        self.api_key = os.getenv("API", "")

        docs = [
            "Python это язык программирования.",
            "requests это библиотека Python для HTTP запросов GET POST PUT DELETE.",
            "POST отправляет данные серверу.",
            "Qdrant это векторная база данных.",
            "Docker это контейнеризация.",
        ]

        vectors = list(self.embedder.embed(docs))

        self.qdrant.create_collection(
            collection_name="wiki",
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )

        self.qdrant.upsert(
            collection_name="wiki",
            points=[
                PointStruct(id=i, vector=vectors[i], payload={"text": docs[i]})
                for i in range(len(docs))
            ],
        )

    def ask(self, question):
        vector = list(self.embedder.embed([question]))[0]

        result = self.qdrant.query_points(
            collection_name="wiki", query=vector, limit=3
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
