from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union

class LyrInfoInCtlgSave(BaseModel):
    layer_id: str
    points_color: str = Field(
        ..., description="Color name for the layer points, e.g., 'red'"
    )


class CtlgMetaData(BaseModel):
    prdcer_ctlg_name: str
    subscription_price: str
    ctlg_description: str
    total_records: int
    ctlg_owner_user_id: str

class PrdcerCtlg(CtlgMetaData):
    lyrs: List[LyrInfoInCtlgSave] = Field(..., description="list of layer objects.")
    display_elements: dict[str, Any] = Field(default_factory=dict, description="Flexible field for frontend to store arbitrary key-value pairs")


class UserId(BaseModel):
    user_id: str

class BooleanQuery(BaseModel):
    boolean_query: Optional[str] = ""
