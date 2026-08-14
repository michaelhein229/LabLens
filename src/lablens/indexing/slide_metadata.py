from urllib.parse import urlsplit, urlunsplit

from lablens.models import SlideTextRecord

def build_slide_chunk_id(record: SlideTextRecord) -> str:
    return f"{record.file_id}:slide:{record.slide_id}"

def build_slide_citation_url(record: SlideTextRecord) -> str:
    parsed_url = urlsplit(record.source_url)
    slide_fragment = f"slide=id.{record.slide_id}"

    return urlunsplit(parsed_url._replace(fragment=slide_fragment))