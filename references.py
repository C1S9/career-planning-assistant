"""Check source identities; this does not prove factual entailment or suitability."""

import re


class ReferenceError(ValueError):
    """Model output used a source identity the application cannot support."""


def validate_references(text: str, evidence, *, required: bool = True) -> None:
    """Reject invented source IDs, external links, and missing required citations."""
    allowed_ids = {source.id for source in evidence.sources}
    allowed_urls = {source.url for source in evidence.sources}
    identifiers = set(re.findall(r"\[(S\d+)\]", text))
    if identifiers - allowed_ids:
        raise ReferenceError("A source identifier was not retrieved for this reply.")
    if required and not identifiers:
        raise ReferenceError("A retrieved source was not cited in this reply.")
    # Links belong to the application's source list. A model may repeat one of
    # those exact links, but cannot silently add an invented or unsafe target.
    links = re.findall(r"\]\(\s*([^\s)]+)", text)
    links += re.findall(r"https?://[^\s<>\]\)\"']+", text)
    if any(link.rstrip(".,;:") not in allowed_urls for link in links):
        raise ReferenceError("A link was not retrieved for this reply.")
