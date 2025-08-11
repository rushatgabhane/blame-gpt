import logging

from libs import constants
from libs.llm import llmNano
from libs.prompt_templates.command_classification import command_classification_parser, command_classifier_prompt
from models.enums import CommandName
from models.models import CommandClassification

logger = logging.getLogger(__name__)


def classify_command(comment_body: str, subject_type: str) -> CommandName:
    """Classify a comment to determine which command to execute."""
    words = comment_body.split()
    user_tag_pos = next((i for i, word in enumerate(words) if constants.USER_TAG.lower() in word.lower()), None)

    if user_tag_pos:
        start = max(0, user_tag_pos - 10)
        end = min(len(words), user_tag_pos + 20)
        relevant_words = words[start:end]
    else:
        relevant_words = words[:50]

    comment_trimmed = " ".join(relevant_words)

    try:
        input = command_classifier_prompt.format(
            comment=comment_trimmed,
            type=subject_type,
            user_tag=constants.USER_TAG,
        )
        response = llmNano.invoke(input)
        classification: CommandClassification = command_classification_parser.invoke(response)
        return CommandName(classification.command_name)
    except Exception as e:
        logger.error(f"failed to classify command for comment {comment_trimmed}: {e}")
        return CommandName.UNKNOWN


def has_again_keyword(comment_body: str) -> bool:
    """Check if comment contains 'again' keyword."""
    return "again" in comment_body.lower()
