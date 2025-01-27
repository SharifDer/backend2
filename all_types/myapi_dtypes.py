from typing import Dict, List, TypeVar, Generic, Optional, Any
from fastapi import UploadFile, File
from pydantic import BaseModel, Field

from all_types.response_dtypes import LyrInfoInCtlgSave

U = TypeVar("U")


class ReqModel(BaseModel, Generic[U]):
    message: str
    request_info: Dict
    request_body: U


class ReqCityCountry(BaseModel):
    city_name: str
    country_name: str


class boxmapProperties(BaseModel):
    name: str
    rating: float
    address: str
    phone: str
    website: str
    business_status: str
    user_ratings_total: int


class ReqSavePrdcerCtlg(BaseModel):
    prdcer_ctlg_name: str
    subscription_price: str
    ctlg_description: str
    total_records: int
    lyrs: List[LyrInfoInCtlgSave] = Field(..., description="list of layer objects.")
    user_id: str
    # thumbnail_url: str
    display_elements: dict
    catalog_layer_options: dict


class ZoneLayerInfo(BaseModel):
    lyr_id: str
    property_key: str


class ReqCatalogId(BaseModel):
    catalogue_dataset_id: str


class ReqUserId(BaseModel):
    user_id: str


class ReqPrdcerLyrMapData(BaseModel):
    prdcer_lyr_id: Optional[str] = ""
    user_id: str


class ReqSavePrdcerLyer(ReqPrdcerLyrMapData):
    prdcer_layer_name: str
    bknd_dataset_id: str
    points_color: str
    layer_legend: str
    layer_description: str
    city_name: str


class ReqFetchDataset(ReqCityCountry, ReqPrdcerLyrMapData):
    boolean_query: Optional[str] = ""
    action: Optional[str] = ""
    page_token: Optional[str] = ""
    search_type: Optional[str] = "default"
    text_search: Optional[str] = ""
    zoom_level: Optional[int] = 0


class ReqFetchCtlgLyrs(BaseModel):
    prdcer_ctlg_id: str
    as_layers: bool
    user_id: str


class ReqCostEstimate(ReqCityCountry):
    included_categories: List[str]
    excluded_categories: List[str]


class Coordinate(BaseModel):
    lat: float
    lng: float


class ReqStreeViewCheck(Coordinate):
    pass


class ReqGeodata(Coordinate):
    bounding_box: list[float]


class ReqLocation(Coordinate):
    radius: float
    bounding_box: list[float]
    page_token: Optional[str] = ""
    text_search: Optional[str] = ""
    boolean_query: Optional[str] = ""
    zoom_level: Optional[int] = 0


class ReqNearestRoute(ReqPrdcerLyrMapData):
    points: List[Coordinate]


class ReqCustomData(ReqCityCountry):
    boolean_query: Optional[str] = ""
    page_token: Optional[str] = ""
    included_types: list[str] = []
    excluded_types: list[str] = []
    zoom_level: Optional[int] = 0


class ReqGradientColorBasedOnZone(BaseModel):
    color_grid_choice: list[str]
    change_lyr_id: str
    change_lyr_name: str
    based_on_lyr_id: str
    based_on_lyr_name: str
    coverage_value: float  # [10min , 20min or 300 m or 500m]
    coverage_property: str  # [Drive_time or Radius]
    color_based_on: str  # ["rating" or "user_ratings_total"]
