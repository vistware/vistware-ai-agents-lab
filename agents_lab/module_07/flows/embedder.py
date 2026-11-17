from pydantic_ai import Embedder

from agents_lab.module_07.settings import module_settings

embedder = Embedder(model=module_settings.EMBEDDER_MODEL)
