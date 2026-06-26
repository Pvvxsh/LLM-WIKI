from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import httpx
import os


class VectorSBERT:

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant = QdrantClient(":memory:")
        self.api_key = os.getenv("API", "")

        docs = [
            "Python это язык программирования высокого уровня.",
            "JavaScript используется для веб-разработки и серверных приложений.",
            "React это библиотека для создания пользовательских интерфейсов.",
            "Docker позволяет упаковывать приложения в контейнеры.",
            "Git — система контроля версий для отслеживания изменений в коде.",
            "PostgreSQL — объектно-реляционная система управления базами данных.",
            "REST API — архитектурный стиль для проектирования веб-сервисов.",
            "Machine Learning — метод обучения компьютеров на данных.",
            "Kubernetes — система оркестрации контейнеров.",
            "Linux — семейство операционных систем.",
        ]

        vectors = self.model.encode(docs).tolist()

        self.qdrant.create_collection(
            collection_name="sbert",
            vectors_config=VectorParams(size=len(vectors[0]), distance=Distance.COSINE),
        )

        self.qdrant.upsert(
            collection_name="sbert",
            points=[
                PointStruct(id=i, vector=vectors[i], payload={"text": docs[i]})
                for i in range(len(docs))
            ],
        )

    def ask(self, question):
        vector = self.model.encode([question])[0].tolist()

        result = self.qdrant.query_points(
            collection_name="sbert", query=vector, limit=3
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
