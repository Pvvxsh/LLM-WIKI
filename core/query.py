class QueryManager:

    def __init__(self):
        self.query = None


    def set_query(self, query: str):

        self.query = query.strip()

        return self.query


    def get_query(self):

        return self.query