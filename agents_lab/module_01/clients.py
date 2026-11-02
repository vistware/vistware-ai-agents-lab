from dataclasses import dataclass

from openai import OpenAI
from openai.types.conversations.conversation import Conversation
from openai.types.responses.response import Response

from agents_lab.module_01.settings import module_settings


@dataclass
class VistwareOpenAIClient:
    instructions: str

    def __post_init__(self) -> None:
        self._client = OpenAI(api_key=module_settings.OPENAI_API_KEY.get_secret_value())
        self._current_conversation: Conversation | None = None

    def ask(self, prompt: str) -> Response:
        if self._current_conversation is None:
            self._current_conversation: Conversation = (
                self._client.conversations.create()
            )
        return self._client.responses.create(
            model=module_settings.AI_MODEL.removeprefix("openai:"),
            instructions=self.instructions,
            input=prompt,
            conversation=self._current_conversation.id,
        )

    def delete_conversation(self) -> None:
        if self._current_conversation is not None:
            self._client.conversations.delete(
                conversation_id=self._current_conversation.id
            )
            self._current_conversation = None
