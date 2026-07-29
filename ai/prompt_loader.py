from pathlib import Path


class PromptLoader:

    def __init__(self):
        self.prompts_dir = Path(__file__).parent / "prompts"

    def load(self, prompt_name: str, **variables) -> str:

        prompt_path = self.prompts_dir / f"{prompt_name}.md"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_name}")

        prompt = prompt_path.read_text(encoding="utf-8")

        for key, value in variables.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        return prompt