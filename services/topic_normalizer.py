class TopicNormalizer:
    ALIASES={
        "developer tool":"Developer Tools",
        "developer tools":"Developer Tools",
        "developer utilities":"Developer Tools",
        "ai agent":"AI Agents",
        "ai agents":"AI Agents",
        "mcp":"Model Context Protocol",
        "model context protocol":"Model Context Protocol",
        "llm":"Large Language Models",
        "large language model":"Large Language Models",
        "large language models":"Large Language Models",
        "web browser":"Browser",
        "browser":"Browser",
    }
    def normalize(self,topic:str)->str:
        if not topic:return ""
        t=topic.strip()
        return self.ALIASES.get(t.lower(),t)
