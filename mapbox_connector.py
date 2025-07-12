from all_types.google_dtypes import GglResponse
from all_types.response_dtypes import GeoJson
from fastapi import HTTPException

from popularity_algo import (
    RADIUS_ZOOM_MULTIPLIER,
    calculate_category_multiplier,
)


class MapBoxConnector:

    @classmethod
    def assign_point_properties(cls, place, with_ids=True):
        lng = place.get("location", {}).get("longitude", 0)
        lat = place.get("location", {}).get("latitude", 0)

        # Construct the properties dictionary with specifically selected keys
        properties = {
            "name": place.get("displayName", {}).get("text", ""),
            "rating": place.get("rating", ""),
            "address": place.get("formattedAddress", ""),
            "phone": place.get("internationalPhoneNumber", ""),
            "types": place.get("types", ""),
            "priceLevel": place.get("priceLevel", ""),
            "primaryType": place.get("primaryType", ""),
            "user_ratings_total": place.get("userRatingCount", ""),
            "heatmap_weight": 1,
        }

        if properties["name"] == "":
            properties["name"] = place.get("name", "")

        # Add the "id" property if with_ids is True
        if with_ids:
            properties["id"] = place.get("id", "")

        # Create a set of keys that have already been handled
        handled_keys = {
            "displayName",
            "rating",
            "formattedAddress",
            "internationalPhoneNumber",
            "types",
            "priceLevel",
            "primaryType",
            "userRatingCount",
            "location",
            "name",
            "id",
        }

        # Add all other keys from place that aren't already handled
        for key, value in place.items():
            if key not in handled_keys:
                properties[key] = value

        return {
            "type": "Feature",
            "properties": properties,
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
        }

    @classmethod
    async def new_ggl_to_boxmap(
        cls, ggl_api_resp, radius, with_ids=True
    ) -> GeoJson:
        if (
            not ggl_api_resp
        ):  # This will handle None, empty string, or empty list
            return GeoJson(
                type="FeatureCollection", features=[], properties=[]
            ).model_dump()

        features = [
            cls.assign_point_properties(place, with_ids)
            for place in ggl_api_resp
        ]

        # Get property keys from the first feature if features exist
        feature_properties = []
        if features:
            # Extract all property keys from the first feature's properties
            feature_properties = list(features[0]["properties"].keys())

        zoom_multiplier = RADIUS_ZOOM_MULTIPLIER.get(radius, 1)

        for idx, feature in enumerate(features):
            feature["properties"]["popularity_score"] = int(
                calculate_category_multiplier(idx) * zoom_multiplier
            )

        business_data = GeoJson(
            type="FeatureCollection",
            features=features,
            properties=feature_properties,
        )
        return business_data.model_dump()
