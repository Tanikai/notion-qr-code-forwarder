from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from typing import Annotated
from ..dependencies.notion import NotionForwarder, get_notion_forwarder
from ..model.mappings import ForwardedDatabase


router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "This is the root of the redirect router"}

@router.get("/{database_name}/{item_id}")
async def read_item(database_name: str,
                    item_id: str,
                    forwarder: Annotated[NotionForwarder, Depends(get_notion_forwarder)]
                    ):
    
    if database_name not in forwarder.forwardings:
        return HTTPException(status_code=404, detail="Database not found")
    
    database: ForwardedDatabase = forwarder.forwardings[database_name]

    if item_id not in database.forwarding_dict:
        return HTTPException(status_code=404, detail="Item ID not found")
    
    urls = database.forwarding_dict[item_id].urls

    if len(urls) == 0:
        return HTTPException(status_code=500, detail=f"No URLs found for item ID {item_id}")
    
    if len(urls) == 1:
        response = RedirectResponse(url=urls[0])
        return response

    return {"message": "multiple URLs found", "urls": urls}
