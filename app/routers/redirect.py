from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from typing import Annotated
from ..dependencies.notion import NotionForwarder, get_notion_forwarder, ItemNotFoundException, \
    DatabaseNotFoundException

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "This is the root of the redirect router"}


@router.get("/{database_name}/{item_id}")
async def read_item(database_name: str,
                    item_id: str,
                    forwarder: Annotated[NotionForwarder, Depends(get_notion_forwarder)]
                    ):
    try:
        urls = await forwarder.get_forwarding_refreshed(database_name, item_id)
        if len(urls) == 0:
            # try refresh from database
            urls = await forwarder.get_forwarding_refreshed(database_name, item_id)

        if len(urls) == 1:
            response = RedirectResponse(url=urls[0])
            return response

        return {"message": "multiple URLs found", "urls": urls}

    except DatabaseNotFoundException as e:
        return HTTPException(status_code=404, detail=str(e))
    except ItemNotFoundException as e:
        return HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
