from typing import Dict, List, TypeVar, Generic, Optional
from fastapi import UploadFile

from pydantic import BaseModel, Field

from all_types.internal_types import PrdcerCtlg, UserId, BooleanQuery

U = TypeVar("U")


class Coordinate(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None


class ReqModel(BaseModel, Generic[U]):
    message: str
    request_info: Dict
    request_body: U


class ReqCityCountry(BaseModel):
    city_name: Optional[str] = None
    country_name: Optional[str] = None


class boxmapProperties(BaseModel):
    name: str
    rating: float
    address: str
    phone: str
    website: str
    business_status: str
    user_ratings_total: int


class ReqSavePrdcerCtlg(PrdcerCtlg, UserId):
    image: Optional[UploadFile] = None


class ReqDeletePrdcerCtlg(UserId):
    prdcer_ctlg_id: str


class ReqDeletePrdcerCtlg(UserId):
    prdcer_ctlg_id: str


class ZoneLayerInfo(BaseModel):
    lyr_id: str
    property_key: str


class ReqCatalogId(BaseModel):
    catalogue_dataset_id: str


class ReqPrdcerLyrMapData(UserId):
    prdcer_lyr_id: Optional[str] = ""


class ReqSavePrdcerLyer(ReqPrdcerLyrMapData):
    prdcer_layer_name: str
    bknd_dataset_id: str
    points_color: str
    layer_legend: str
    layer_description: str
    city_name: str


class ReqDeletePrdcerLayer(BaseModel):
    user_id: str
    prdcer_lyr_id: str


class ReqFetchDataset(ReqCityCountry, ReqPrdcerLyrMapData, Coordinate):
    boolean_query: Optional[str] = ""
    action: Optional[str] = ""
    page_token: Optional[str] = ""
    search_type: Optional[str] = "category_search"
    text_search: Optional[str] = ""
    zoom_level: Optional[int] = 0
    radius: Optional[float] = 30000.0
    bounding_box: Optional[list[float]] = []
    included_types: Optional[list[str]] = []
    excluded_types: Optional[list[str]] = []
    ids_and_location_only: Optional[bool] = False
    include_rating_info: Optional[bool] = False
    include_only_sub_properties: Optional[bool] = True
    full_load: Optional[bool] = False


class ReqFetchCtlgLyrs(BaseModel):
    prdcer_ctlg_id: str
    as_layers: bool
    user_id: str


class ReqCostEstimate(ReqCityCountry):
    included_categories: List[str]
    excluded_categories: List[str]


class ReqStreeViewCheck(Coordinate):
    pass


class ReqGeodata(Coordinate):
    bounding_box: list[float]


class ReqNearestRoute(ReqPrdcerLyrMapData):
    points: List[Coordinate]


class ReqColorBasedon(BaseModel):
    change_lyr_id: str
    change_lyr_name: str
    change_lyr_current_color: str = "#CCCCCC"
    change_lyr_new_color: str = "#FFFFFF"
    based_on_lyr_id: str
    based_on_lyr_name: str
    area_coverage_value: float  # [10min , 20min or 300 m or 500m]
    area_coverage_measure: str  # [Drive_time or Radius]
    evaluation_property_name: str  # ["rating" or "user_ratings_total"]
    evaluation_comparison_operator: str
    color_grid_choice: Optional[List[str]] = []
    evaluation_name_list: Optional[List[str]] = []


class ReqFilterBasedon(ReqColorBasedon):
    property_threshold: float | str


class LayerReference(BaseModel):
    id: str
    name: str


# User prompt -> llm
class ReqLLMEditBasedon(BaseModel):
    user_id: str
    layers: List[LayerReference] = Field(..., description="List of layers with required id and name fields")
    prompt: str


class ResValidationResult(BaseModel):
    is_valid: bool
    reason: Optional[str] = None
    suggestions: Optional[List[str]] = None
    endpoint: Optional[str] = None
    body: ReqColorBasedon = None
    recolor_result: Optional[List] = None


class ReqLLMFetchDataset(BaseModel):
    """Extract Location Based Information from the Query"""

    query: str = Field(
        default="", description="Original query passed by the user."
    )


class ReqSrcDistination(BaseModel):
    source: Coordinate
    destination: Coordinate


class ReqIntelligenceData(BaseModel):
    min_lng: float
    min_lat: float
    max_lng: float
    max_lat: float
    zoom_level: int
    user_id: str
    population: Optional[bool]
    income: Optional[bool]


class ReqClustersForSalesManData(BooleanQuery, UserId, ReqCityCountry):
    num_sales_man: int
    distance_limit: float = 2.5
    include_raw_data: bool = False


class ReqHubExpansion(BaseModel):
    """Default configuration for hub expansion analysis"""

    # Location context
    city_name: str = "Riyadh"
    country_name: str = "Saudi Arabia"
    analysis_bounds: Optional[dict] = {}

    # Target destinations
    target_search: str = "@الحلقه@"
    max_target_distance_km: float = 5.0
    max_target_time_minutes: int = 8
    search_type: str = "keyword_search"

    # Competitor analysis
    competitor_name: str = "@نينجا@"
    competitor_analysis_radius_km: float = 2.0
    search_type: str = "keyword_search"

    # Hub requirements
    hub_type: str = "warehouse_for_rent"
    min_facility_size_m2: Optional[int] = None
    max_rent_per_m2: Optional[float] = None
    search_type: str = "category_search"

    # Population requirements
    max_population_center_distance_km: float = 10.0
    max_population_center_time_minutes: int = 15
    min_population_threshold: int = 1000

    # Analysis parameters
    scoring_weights: Dict[str, float] = {
        "target_proximity": 0.35,
        "population_access": 0.30,
        "rent_efficiency": 0.10,
        "competitive_advantage": 0.15,
        "population_coverage": 0.10,
    }

    # Scoring thresholds
    scoring_thresholds: Dict[str, Dict[str, float]] = {
        "target_proximity": {
            "min_score": 0.0,
            "max_score": 10.0,
            "penalty_multiplier": 1.0,
        },
        "population_access": {
            "min_score": 0.0,
            "max_score": 10.0,
            "accessibility_bonus_max": 3.0,
        },
        "rent_efficiency": {"min_score": 0.0, "max_score": 10.0},
        "competitive_advantage": {
            "min_score": 2.0,
            "max_score": 10.0,
            "density_penalty_max": 5.0,
        },
        "population_coverage": {"min_score": 0.0, "max_score": 10.0},
    }

    # Coverage methodology
    density_thresholds: Dict[str, Dict[str, float]] = {
        "very_high_density": {
            "threshold": 8000,
            "radius_km": 2.0,
            "max_delivery_minutes": 20,
        },
        "high_density": {
            "threshold": 4000,
            "radius_km": 3.5,
            "max_delivery_minutes": 25,
        },
        "medium_density": {
            "threshold": 2000,
            "radius_km": 5.0,
            "max_delivery_minutes": 30,
        },
        "low_density": {
            "threshold": 0,
            "radius_km": 8.0,
            "max_delivery_minutes": 40,
        },
    }

    # Output preferences
    top_results_count: int = 5
    include_route_optimization: bool = True
    include_market_analysis: bool = True
    include_success_metrics: bool = True

    # User context
    user_id: str = "default_user"
