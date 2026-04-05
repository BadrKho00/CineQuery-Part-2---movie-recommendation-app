import re


def fix_title(raw: str) -> str:
    """
    Convert MovieLens title format to natural reading order.
    Examples:
        "Matrix, The (1999)"      -> "The Matrix (1999)"
        "Grumpier Old Men (1995)" -> "Grumpier Old Men (1995)"   (unchanged)
        "NaN" / None              -> ""
    """
    if not raw or not isinstance(raw, str):
        return ""

    # Extract just the 4-digit year from suffix, e.g. "(1999)" -> "1999"
    year_match = re.search(r"\s*\((\d{4})\)\s*$", raw)
    year = year_match.group(1) if year_match else ""
    base = raw[: year_match.start()].strip() if year_match else raw.strip()

    # Move trailing article back to front: "Title, The" -> "The Title"
    article_match = re.search(r",\s*(The|A|An)$", base, re.IGNORECASE)
    if article_match:
        article = article_match.group(1).capitalize()
        base = f"{article} {base[:article_match.start()].strip()}"

    return f"{base} ({year})" if year else base
