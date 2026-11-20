from pydantic_ai import Embedder

from agents_lab.module_07.settings import module_settings

embedding_client = Embedder(model=module_settings.EMBEDDER_MODEL)
