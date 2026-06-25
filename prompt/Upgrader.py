import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.query import QueryManager
from llm.send import prompt_generate_async

query_manager = QueryManager()


async def upg():
    query = query_manager.get_query()
    result = await prompt_generate_async(query)
    return result
