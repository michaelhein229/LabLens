def normalize_text(raw_text: str) -> str:
    """
    Normalize the input text by performing the following operations:
    1. Convert to lowercase.
    2. Remove leading and trailing whitespace.
    3. Replace multiple spaces with a single space.
    4. Remove punctuation.

    Args:
        raw_text (str): The raw input text to be normalized.

    Returns:
        str: The normalized text.
    """
    import re
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.strip()

    cleaned_lines = []

    for line in normalized.split("\n"):
        line = re.sub(r"[ \t]+", " ", line.strip())
        cleaned_lines.append(line)

    normalized = "\n".join(cleaned_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized