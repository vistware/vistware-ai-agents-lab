
import os

from pydantic import BaseModel, Field
from pydantic_ai import Agent, UsageLimits


class LearningResponse(BaseModel):
    answer: str
    concepts: list[str] = Field(
        min_length=2,
        max_length=2,
    )


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    agent = Agent(
        os.getenv("AI_MODEL", "openai:gpt-5-mini"),
        output_type=LearningResponse,
        instructions=(
            "You are an AI engineering teacher. "
            "Always respond in Polish. "
            "Keep answers short and precise."
        ),
    )

    result = agent.run_sync(
        (
            "Wyjaśnij w jednym zdaniu, czym jest agent AI. "
            "Podaj dokładnie dwa powiązane z nim pojęcia."
        ),
        usage_limits=UsageLimits(request_limit=3),
    )

    print("Structured response:")
    print(result.output.model_dump_json(indent=2))

    print("\nToken usage:")
    print(result.usage)


if __name__ == "__main__":
    main()
