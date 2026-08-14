from pydantic import AwareDatetime, BaseModel


class DriveFileMetadata(BaseModel):
    file_id: str
    file_name: str
    mime_type: str
    created_time: AwareDatetime
    modified_time: AwareDatetime
    web_url: str
    folder_id: str

class SlideTextRecord(BaseModel):
    file_id: str
    presentation_title: str
    slide_number: int
    slide_id: str
    text: str
    modified_time: AwareDatetime
    source_url: str

# class DocumentChunk(BaseModel):
#     chunk_id: str
#     file_id: str
#     source_type: str
#     source_title: str
#     source_position: int
#     source_element_id: str
#     raw_text: str
