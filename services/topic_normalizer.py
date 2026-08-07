from __future__ import annotations


class TopicNormalizer:
    """Normalize semantically similar topic labels into stable canonical names."""

    ALIASES: dict[str, str] = {
        # Developer ecosystem
        "developer tool": "Developer Tools",
        "developer tools": "Developer Tools",
        "developer utilities": "Developer Tools",
        "developer infrastructure": "Developer Tools",
        "developer productivity": "Developer Tools",
        "developer workflow": "Developer Tools",
        "developer experience": "Developer Tools",
        "developer platform": "Developer Tools",
        "developer environment": "Developer Tools",
        "developer tooling": "Developer Tools",
        "developer ops": "Developer Tools",

        # AI agents
        "ai agent": "AI Agents",
        "ai agents": "AI Agents",
        "ai agent orchestration": "AI Agents",
        "ai agent framework": "AI Agents",
        "agent orchestration": "AI Agents",
        "agent framework": "AI Agents",
        "agent runtime": "AI Agents",

        # Protocol / models
        "mcp": "Model Context Protocol",
        "model context protocol": "Model Context Protocol",
        "llm": "Large Language Models",
        "large language model": "Large Language Models",
        "large language models": "Large Language Models",

        # Browser
        "browser": "Browser",
        "web browser": "Browser",
        "browser automation": "Browser",

        # Desktop software
        "desktop automation": "Desktop Software",
        "desktop productivity": "Desktop Software",
        "desktop ui customization": "Desktop Software",
        "desktop software": "Desktop Software",

        # Coding assistants
        "openai codex": "Coding Assistants",
        "codex": "Coding Assistants",
        "coding assistant": "Coding Assistants",
        "coding assistants": "Coding Assistants",

        # Open source
        "open source": "Open Source",
        "open-source": "Open Source",

        # Collaboration
        "slack integration": "Slack Integrations",
        "slack integrations": "Slack Integrations",
    }

    def normalize(self, topic: str | None) -> str:
        if topic is None:
            return ""

        text = " ".join(
            str(topic)
            .replace("/", " ")
            .replace("_", " ")
            .split()
        ).strip(" -•")

        if not text:
            return ""

        return self.ALIASES.get(text.lower(), text)

    def normalize_many(self, topics: list[str] | None) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for topic in topics or []:
            normalized = self.normalize(topic)

            if not normalized:
                continue

            key = normalized.lower()

            if key in seen:
                continue

            seen.add(key)
            result.append(normalized)

        return result
