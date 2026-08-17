from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


class TemplateEngine:

    def render(self, template_path: str, context: dict) -> str:
        template = (ROOT_DIR / template_path).read_text(
            encoding="utf-8"
        )

        for key, value in context.items():
            template = template.replace(
                "{{ " + key + " }}",
                str(value),
            )

        return template
