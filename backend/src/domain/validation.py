import re

TOOL_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{0,199}$")


def validate_tool_name(name: str) -> str:
    if not TOOL_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            f"Invalid tool name '{name}': must start with a letter, "
            "contain only alphanumeric characters and underscores, max 200 chars"
        )
    return name
