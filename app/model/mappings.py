from typing import List, Dict
from dataclasses import dataclass, field


@dataclass
class ForwardMapping():
    item_id: str = "" # id that is passed in the request to the service
    notion_url: str = "" # corresponding notion url


@dataclass
class ForwardUrls():
    urls: List[str] # List of urls with the item_id

@dataclass
class ForwardedDatabase():
    name: str = "" # Name of the database (used in request path)
    database_id: str = "" # GUID of notion database
    forward_column_name: str = "" # Column where the IDs are retrieved

    # auto forward if only single URL
    # warning / error if multiple URLs
    forwarding_dict: Dict[str, ForwardUrls] = field(default_factory=lambda: {}) # key: item_id




 