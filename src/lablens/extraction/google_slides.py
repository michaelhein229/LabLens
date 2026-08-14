from lablens.models import DriveFileMetadata, SlideTextRecord

def extract_text_from_slide(slide: dict) -> str:
    parts = []

    for element in slide.get("pageElements", []):
        shape = element.get("shape", {})
        text = shape.get("text", {})
        text_elements = text.get("textElements", [])

        for text_element in text_elements:
            text_run = text_element.get("textRun")
            if text_run:
                parts.append(text_run.get("content",""))

    return "".join(parts).strip()

def extract_slide_text_records(
    presentation: dict,
    file_metadata: DriveFileMetadata,
) -> list[SlideTextRecord]:
    records = []

    for index, slide in enumerate(presentation.get("slides", []), start=1):
        record = SlideTextRecord(
            file_id=file_metadata.file_id,
            presentation_title=presentation.get("title", ""),
            slide_number=index,
            slide_id=slide.get("objectId"),
            text=extract_text_from_slide(slide),
            modified_time=file_metadata.modified_time,
            source_url=file_metadata.web_url
        )
        records.append(record)

    return records

def extract_google_slides(
        slides_service,
        file_metadata: DriveFileMetadata
) -> list[SlideTextRecord]:
    presentation = slides_service.presentations().get(
        presentationId=file_metadata.file_id
    ).execute()

    return extract_slide_text_records(presentation, file_metadata)