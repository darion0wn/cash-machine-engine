from pathlib import Path


class TemplateEngine:

    def render(self, template_path: str, context: dict) -> str:

        template = Path(template_path).read_text(encoding="utf-8")

        for key, value in context.items():
            template = template.replace(
                "{{ " + key + " }}",
                str(value)
            )

        return template