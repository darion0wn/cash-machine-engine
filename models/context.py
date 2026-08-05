from dataclasses import dataclass


@dataclass
class Context:

    title: str

    article: str = ""

    readme: str = ""

    website: str = ""

    meta_description: str = ""

    pricing: str = ""

    faq: str = ""

    comments: str = ""

    source_description: str = ""