from typing import List
from all_types.request_dtypes import ReqFetchDataset

TOKEN_SEPARATOR = "@#$"

def make_ggl_layer_filename(req: ReqFetchDataset) -> str:
    # type_string = make_include_exclude_name(req.includedTypes, req.excludedTypes)
    type_string = req.boolean_query.replace(" ", "_")
    tcc_string = f"{type_string}_{req.country_name}_{req.city_name}"
    return tcc_string


def make_include_exclude_name(include_list, exclude_list):
    excluded_str = ",".join(exclude_list)
    included_str = ",".join(include_list)

    type_string = f"include={included_str}_exclude={excluded_str}"
    return type_string


def make_ggl_dataset_cord_string(lng: str, lat: str, radius: str):
    return f"{lng}_{lat}_{radius}"


def make_dataset_filename(req: ReqFetchDataset) -> str:
    if req:
        cord_string = make_ggl_dataset_cord_string(req.lng, req.lat, req.radius)
        # type_string = make_include_exclude_name(req.includedTypes, req.excludedTypes)
        type_string = req.boolean_query.replace(" ", "_")
        try:
            name = f"{cord_string}_{type_string}_token={req.page_token}"
        except AttributeError as e:
            raise ValueError(f"Invalid location request object: {str(e)}")

    return name


def make_dataset_filename_part(
    req: ReqFetchDataset, included_types: List[str], excluded_types: List[str]
) -> str:
    """Generate unique dataset ID based on query terms."""
    cord_string = make_ggl_dataset_cord_string(req.lng, req.lat, req.radius)
    type_string = ""
    if included_types:
        include_str = "_".join(sorted(included_types))
        type_string = type_string + f"including_{include_str}"
    if excluded_types:
        exclude_str = "_".join(sorted(excluded_types))
        type_string = type_string + f"excluding_{exclude_str}"
    return f"{cord_string}_{type_string}"


async def get_plan_name_and_index(page_token: str):
    plan_name, current_plan_index = page_token.split(f"{TOKEN_SEPARATOR}")
    _, plan_name = plan_name.split("page_token=")
    current_plan_index = int(current_plan_index)
    return plan_name, current_plan_index


async def make_next_page_token_name(plan_name, index: int):
    next_page_token = f"page_token={plan_name}{TOKEN_SEPARATOR}{index}"
    return next_page_token


async def make_plan_name(req: ReqFetchDataset):
    """Create a plan name based on the request parameters."""
    tcc_string = make_ggl_layer_filename(req)
    plan_name = f"plan_{tcc_string}"
    return plan_name