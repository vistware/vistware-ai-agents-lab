from decimal import Decimal
from typing import Any

from pydantic import ValidationError
from pydantic_ai import AgentRunResult, ConversationTypeAdapter, UsageLimits
from pydantic_ai.conversation import Conversation

from agents_lab.module_06.agents import vistware_incident_investigator
from agents_lab.module_06.dependencies import project_init
from agents_lab.module_06.settings import module_settings


def print_metrics(result: AgentRunResult[Any]) -> None:
    usage = result.usage

    print(f"\n{'=' * 50}")
    print("METRICS")
    print(f"{'=' * 50}")

    print(f"Model requests:       {usage.requests}")
    print(f"Tool calls:           {usage.tool_calls}")
    print(f"Input tokens:         {usage.input_tokens:,}")
    print(f"Output tokens:        {usage.output_tokens:,}")
    print(f"Reasoning tokens:     {usage.output_reasoning_tokens:,}")
    print(f"Total tokens:         {usage.total_tokens:,}")
    print(f"Cache read tokens:    {usage.cache_read_tokens:,}")
    print(f"Cache hit ratio:      {usage.cache_hit_ratio:.1%}")

    cost = f"${usage.cost:.6f}" if usage.cost is not None else "N/A"
    print(f"Estimated cost:       {cost}")

    print(f"All messages:         {len(result.all_messages())}")
    print(f"New messages:         {len(result.new_messages())}")
    print(f"{'=' * 50}\n")


def get_last_conversation() -> Conversation | None:
    try:
        return ConversationTypeAdapter.validate_json(
            module_settings.CONVERSATION_HISTORY_FILE.read_bytes()
        )
    except ValidationError:
        return None


def main(
    *,
    continue_conversation: bool = False,
) -> None:
    project_init()
    user_questions = [
        "Show open incidents for the identity service.",
        "And which of them have a 'critical' priority?",
        "Prepare a brief summary of our entire analysis.",
    ] * 2
    if continue_conversation:
        last_conversation = get_last_conversation()
    else:
        last_conversation = None
    for user_question in user_questions:
        result = vistware_incident_investigator.run_sync(
            user_prompt=user_question,
            usage_limits=UsageLimits(cost_limit=Decimal("2.0"), request_limit=20),
            conversation=last_conversation,
        )
        last_conversation = result.conversation
        print(result.output.model_dump_json(indent=2))
        print_metrics(result=result)
        module_settings.CONVERSATION_HISTORY_FILE.write_bytes(
            ConversationTypeAdapter.dump_json(last_conversation)
        )
        input("Press Enter to continue...")


if __name__ == "__main__":
    main(continue_conversation=False)
