from decimal import Decimal

from pydantic import ValidationError
from pydantic_ai import ConversationTypeAdapter, UsageLimits
from pydantic_ai.conversation import Conversation

from agents_lab.module_05.agents import vistware_incident_investigator
from agents_lab.module_05.dependencies import project_init
from agents_lab.module_05.settings import module_settings


def get_last_conversation() -> Conversation | None:
    try:
        return ConversationTypeAdapter.validate_json(
            module_settings.CONVERSATION_HISTORY_FILE.read_bytes()
        )
    except ValidationError:
        return None


def main(*, continue_conversation: bool = False) -> None:
    project_init()
    user_questions = [
        "Show open incidents for the identity service.",
        "And which of them have a 'critical' priority?",
        "Prepare a brief summary of our entire analysis.",
    ]
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
        all_messages = result.all_messages()
        new_messages = result.new_messages()
        last_conversation = result.conversation
        print("User question:", user_question)
        print("*****" * 10)
        print("All messages:", all_messages)
        print("*****" * 10)
        print("New messages:", new_messages)
        print("*****" * 10)
        print("Conversation:", last_conversation)
        print("*****" * 10)
        print(result.output.model_dump_json(indent=2))
        module_settings.CONVERSATION_HISTORY_FILE.write_bytes(
            ConversationTypeAdapter.dump_json(last_conversation)
        )
        input("Press Enter to continue...")


if __name__ == "__main__":
    main(continue_conversation=True)
