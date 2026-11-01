from pydantic import BaseModel, Field
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.run import AgentRunResult

from .settings import module_settings


class LearningResponse(BaseModel):
    answer: str
    concepts: list[str] = Field(
        min_length=2,
        max_length=2,
    )


def main() -> None:
    agent = Agent(
        module_settings.AI_MODEL,
        output_type=LearningResponse,
        instructions=(
            "You are an AI engineering teacher. "
            "Always respond in English. "
            "Keep answers short and precise."
        ),
    )

    result: AgentRunResult[LearningResponse] = agent.run_sync(
        user_prompt=(
            "Explain in one sentence what an AI agent is. "
            "Provide exactly two related concepts."
        ),
        usage_limits=UsageLimits(request_limit=3),
    )

    print("Structured response:")
    print(result.output.model_dump_json(indent=2))

    print("\nToken usage:")
    print(result.usage)


if __name__ == "__main__":
    main()
