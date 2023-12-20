import json
import os

class Router:
    def __init__(self):
        self._expert_map = {}

    def register(self, expert, category):
        self._expert_map[category] = expert

    def dispatch(self, query):
        results = []
        for category, expert in self._expert_map.items():
            if expert.can_process(query):
                print(f"Dispatching to {category}")
                results.append(expert.process(query))
        if len(results) == 0:
            return "Query type not recognized."

        # TODO: ask some LLM model to pick the best answer or combine them
        return results
