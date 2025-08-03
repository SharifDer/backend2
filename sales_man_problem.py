import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import box, Polygon
import shapely
from all_types.request_dtypes import (
    ReqIntelligenceData,
    ReqFetchDataset,
    ReqClustersForSalesManData,
)
from storage_methods import fetch_intelligence_by_viewport
from data_fetcher import fetch_country_city_data, fetch_dataset
import contextily as ctx
from typing import Tuple
import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Optional
import time

logger = logging.getLogger(__name__)


def define_boundary(bounding_box: list[tuple[float, float]]) -> Polygon:
    """
    args:
    ----
    A list of tuples containing containing lng, lat information.
    The length of the list must be [3,inf)

    return:
    ------
    A shapely polygon
    """
    boundary = Polygon([[p[0], p[1]] for p in bounding_box])
    return boundary


async def get_population_and_income(
    bounding_box: list[tuple[float, float]], zoom_level: int
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Fetch both population and income data for a specific bounding box and zoom level
    using the API endpoint, making two separate calls.

    Args:
        bounding_box: List of (longitude, latitude) tuples defining the area
        zoom_level: The zoom level to retrieve data for

    Returns:
        Tuple of (population_gdf, income_gdf) GeoDataFrames
    """
    # Calculate bounding box coordinates once
    min_lng = min(point[0] for point in bounding_box)
    max_lng = max(point[0] for point in bounding_box)
    min_lat = min(point[1] for point in bounding_box)
    max_lat = max(point[1] for point in bounding_box)

    # Create base request object with common parameters
    base_request = {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
        "zoom_level": zoom_level,
        "user_id": "your_user_id",  # You'll need to provide this
    }

    # Create population-only request
    population_request = ReqIntelligenceData(
        **base_request, population=True, income=False
    )

    # Create combined population and income request
    income_request = ReqIntelligenceData(**base_request, population=True, income=True)

    # Fetch both datasets concurrently
    population_task = fetch_intelligence_by_viewport(population_request)
    income_task = fetch_intelligence_by_viewport(income_request)

    # Wait for both tasks to complete
    population_data, income_data = await asyncio.gather(population_task, income_task)

    # Process population data
    population_features = population_data.get("features", [])
    population_gdf = (
        gpd.GeoDataFrame.from_features(population_features)
        if population_features
        else gpd.GeoDataFrame()
    )

    # Process income data
    income_features = income_data.get("features", [])
    income_gdf = (
        gpd.GeoDataFrame.from_features(income_features)
        if income_features
        else gpd.GeoDataFrame()
    )

    return population_gdf, income_gdf


def filter_data_by_bounding_box(
    places_data: dict = None,
    bounding_box: list[tuple[float, float]] = None,
) -> gpd.GeoDataFrame:
    """
    Filter places data by a boundary polygon.
    args:
    ----
    `places_data` is the GeoJSON FeatureCollection object (e.g., supermarkets, pharmacies)
    `bounding_box` is the list of lon lat pairs to develop a shapely polygon
    return:
    ------
    GeoDataFrame filtered using bounding box
    """
    # Create GeoDataFrame directly from the GeoJSON FeatureCollection
    places = gpd.GeoDataFrame.from_features(places_data["features"])

    # Create boundary polygon
    city_boundary = define_boundary(bounding_box)

    # Filter by boundary
    places = places[places.within(city_boundary)]

    # Add longitude and latitude columns
    places["longitude"] = places.geometry.x
    places["latitude"] = places.geometry.y
    return places


def create_grid(
    population: gpd.GeoDataFrame | None = None, grid_size: int | None = None
) -> gpd.GeoDataFrame:
    """
    args:
    ----
    `pouplation` is the filtered data set from `get_population_by_zoom_in_bounding_box`
    `grid_size` is the size of the grid. if set None the grid size will be calculated based on the
    available data. donot set its value unless necessary

    return:
    ------
    A dataframe containing geometry column having polygon covering the ROI
    """
    logger.info(f"Starting grid creation with {len(population)} population data points")
    population = population.set_crs("EPSG:4326")

    # Extract the minimum bounding rectangle (MBR) of all population data points
    minx, miny, maxx, maxy = population.total_bounds
    total_area = (maxx - minx) * (maxy - miny)

    logger.info(
        f"Study area bounds: [{minx:.4f}, {miny:.4f}] to [{maxx:.4f}, {maxy:.4f}]"
    )
    logger.info(
        f"Total study area: {total_area:.2f} square degrees ({total_area * 111.32**2:.2f} km² approx)"
    )
    # Calculate optimal grid size using spatial statistical theory
    # Formula: grid_size = √(total_area / number_of_points)
    # This ensures each grid cell represents approximately one data point on average
    # Based on uniform sampling theory and spatial aggregation principles
    # Example: For NYC with 1000 population points over 55km x 45km area:
    # a_grid_size = √((55 * 45) / 1000) = √2.475 ≈ 1.57 km per grid cell
    a_grid_size = (total_area / population.shape[0]) ** 0.5

    logger.info(
        f"Calculated optimal grid size: {a_grid_size:.6f} degrees ({a_grid_size * 111.32:.2f} km)"
    )
    # Use calculated optimal size if no manual override provided
    # Allows for adaptive grid resolution based on data density
    if grid_size is None:
        grid_size = a_grid_size
        logger.info("Using calculated optimal grid size")
    else:
        logger.info(
            f"Using manual grid size: {grid_size:.6f} degrees ({grid_size * 111.32:.2f} km)"
        )

    # Calculate expected number of grid cells
    expected_x_cells = int(np.ceil((maxx - minx) / grid_size))
    expected_y_cells = int(np.ceil((maxy - miny) / grid_size))
    expected_total_cells = expected_x_cells * expected_y_cells

    logger.info(
        f"Expected grid dimensions: {expected_x_cells} × {expected_y_cells} = {expected_total_cells} total cells"
    )
    # Create regular tessellation using systematic sampling theory
    # Generates a fishnet grid of square polygons covering the entire study area
    # Each box(x, y, x+size, y+size) creates a square polygon geometry
    # Uses nested list comprehension for efficient vectorized grid generation
    # Example: For 55km x 45km area with 1.57km grid size = ~35 x 29 = ~1015 grid cells
    grid_cells = [
        box(x, y, x + grid_size, y + grid_size)
        for x in np.arange(minx, maxx, grid_size)
        for y in np.arange(miny, maxy, grid_size)
    ]

    logger.info(
        f"Generated {len(grid_cells)} grid cells (expected {expected_total_cells})"
    )

    # Convert list of geometries to GeoDataFrame with proper coordinate reference system
    # Inherits CRS from population data to maintain spatial accuracy
    grid = gpd.GeoDataFrame(geometry=grid_cells, crs=population.crs)
    logger.info(f"Created grid GeoDataFrame with CRS: {grid.crs}")
    logger.info("Grid creation completed successfully")
    return grid


def haversine(
    lat1_array: np.ndarray,
    lon1_array: np.ndarray,
    lat2_array: np.ndarray,
    lon2_array: np.ndarray,
) -> np.ndarray:
    """
    args:
    `lat1_array, lon1_array, lat2_array, lon2_array` are the arrays of origins and destinations.
    lat1, lon1 are for the origins in degrres (population center)
    lat2, lon2 are for the destination in degrees (places)

    return:
    ------
    A numpy array for distance matrix calculated using haversine formula which takes inaccount the
    curvature of the earth. The returned distances are in km
    """
    logger.info(
        f"Computing Haversine distances: {len(lat1_array)} origins × {len(lat2_array)} destinations"
    )
    logger.info(f"Total distance calculations: {len(lat1_array) * len(lat2_array):,}")
    # Convert decimal degrees to radians for trigonometric calculations
    # All trigonometric functions in numpy work with radians, not degrees
    # Example: 40.7589° → 0.7118 radians, -73.9851° → -1.2915 radians
    lat1_rad, lon1_rad = np.radians(lat1_array), np.radians(lon1_array)
    lat2_rad, lon2_rad = np.radians(lat2_array), np.radians(lon2_array)

    logger.debug("Converted coordinates to radians")
    logger.debug(
        f"Origin latitude range: {np.min(lat1_rad):.4f} to {np.max(lat1_rad):.4f} radians"
    )
    logger.debug(
        f"Origin longitude range: {np.min(lon1_rad):.4f} to {np.max(lon1_rad):.4f} radians"
    )
    # Reshape origin arrays to enable broadcasting for distance matrix computation
    lat1_rad = lat1_rad[:, np.newaxis]
    lon1_rad = lon1_rad[:, np.newaxis]

    logger.debug(
        f"Reshaped arrays for broadcasting: {lat1_rad.shape} × {lat2_rad.shape}"
    )
    # Calculate coordinate differences using broadcasting
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    logger.debug(f"Calculated coordinate differences with shape: {dlat.shape}")

    # Apply Haversine formula for great-circle distances on a sphere
    # Formula: a = sin²(Δφ/2) + cos φ₁ ⋅ cos φ₂ ⋅ sin²(Δλ/2)
    # This accounts for Earth's curvature and provides accurate distances
    # First term: handles latitudinal differences
    # Second term: handles longitudinal differences scaled by latitude cosines
    # Example: For 2.5km distance, a ≈ 0.000039 (very small for short distances)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0) ** 2
    )

    # Complete Haversine formula
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    # Earth's mean radius in kilometers (WGS84 approximation)
    R = 6371.0
    distances = R * c
    logger.info(
        f"Haversine calculation completed. Distance matrix shape: {distances.shape}"
    )
    logger.info(
        f"Distance statistics: min={np.min(distances):.2f}km, max={np.max(distances):.2f}km, mean={np.mean(distances):.2f}km"
    )
    logger.info(
        "This represents realistic Earth-surface distances accounting for planetary curvature"
    )
    return distances


def get_grids_of_data(
    population_gdf: gpd.GeoDataFrame,
    places: gpd.GeoDataFrame,
    weights: gpd.GeoDataFrame,
    distanace_limit: float,
) -> gpd.GeoDataFrame:
    """
    Creates a grid representation of the area and aggregates population and places data within each grid cell,
    calculating accessibility and market potential.

    args:
    ----
    `population_gdf` are the population centers in a form if geodataframe
    `places` are the places geodataframe
    `weights` are the income dataframes in this context for each population center keep `None` if unavailable
    `distance_limit` is a max distance a person is willing to travel to reach destination

    return:
    ------
    a single geodataframe containing polygons (grids) for entire ROI and aggregated data for each grid
    cell (population, places counts)
    """

    # Ensure population data has proper CRS
    logger.info(
        f"Starting grid data aggregation with {len(population_gdf)} population centers, {len(places)} places"
    )
    logger.info(
        f"Distance limit for accessibility: {distanace_limit:.1f}km (typical walking/driving threshold)"
    )
    logger.info(f"Income weights provided: {weights is not None}")

    population_gdf = population_gdf.set_crs("EPSG:4326")
    places = places.set_crs("EPSG:4326")

    # Standardize population data structure for consistent processing
    # Extract centroids as representative points for polygon data
    # This follows spatial analysis principles of point-in-polygon representation
    origins = population_gdf.copy()
    origins["longitude"] = origins.geometry.centroid.x
    origins["latitude"] = origins.geometry.centroid.y
    origins["population"] = origins["Population_Count"]

    total_population = origins["population"].sum()
    logger.info(f"Total population in study area: {total_population:,} people")
    logger.info(
        f"Population density: {total_population/len(origins):.0f} people per population center"
    )
    # Select only essential columns to optimize memory usage and processing speed
    # Follows data science best practices of working with minimal necessary data
    origins = origins[["geometry", "longitude", "latitude", "population"]].reset_index(
        drop=True
    )

    # Prepare destinations dataset with consistent structure
    destinations = places[["geometry", "longitude", "latitude"]].reset_index(drop=True)

    # Compute full distance matrix between all origins and destinations
    logger.info(
        f"Prepared {len(origins)} origins and {len(destinations)} destinations for analysis"
    )

    # Compute full distance matrix between all origins and destinations
    # Uses Haversine formula to account for Earth's curvature
    # Results in M×N matrix where M=origins, N=destinations
    # This implements spatial interaction theory for accessibility analysis
    # Example: 500 population centers × 150 supermarkets = 500×150 matrix with distances 0.2-25.8 km
    matrix = haversine(
        origins.latitude.values,
        origins.longitude.values,
        destinations.latitude.values,
        destinations.longitude.values,
    )

    # Initialize accessibility mapping
    # Initialize accessibility mapping using origin-destination cost matrix
    # Dictionary stores lists of accessible destination indices for each origin
    # This implements the concept of service catchment areas in spatial analysis
    od_cost_matrix = {k: [] for k in range(matrix.shape[0])}

    # Calculate accessibility for each population center
    logger.info("Calculating accessibility for each population center...")

    accessibility_counts = []

    for i in range(matrix.shape[0]):
        od = matrix[i].tolist()

        # Find accessible destinations within distance threshold
        while len(od_cost_matrix[i]) < matrix.shape[1]:
            if np.min(od) < distanace_limit:
                amn = np.argmin(od)
                if np.isfinite(amn):
                    od_cost_matrix[i].append(amn)
                od[amn] = np.inf
            else:
                # Ensure every origin has at least one accessible destination
                if len(od_cost_matrix[i]) == 0:
                    amn = np.argmin(od)
                    if np.isfinite(amn):
                        od_cost_matrix[i].append(amn)
                break

        accessibility_counts.append(len(od_cost_matrix[i]))

    # Calculate accessibility indicator for each population center
    # Counts number of services/facilities reachable within distance limit
    # Higher values indicate better accessibility/service availability
    # Example: Downtown areas might have 8-12 accessible supermarkets, suburban areas 2-4
    origins["number_of_accessibile_markets"] = accessibility_counts

    avg_accessibility = np.mean(accessibility_counts)
    max_accessibility = np.max(accessibility_counts)
    min_accessibility = np.min(accessibility_counts)
    logger.info("Accessibility analysis completed:")
    logger.info(
        f"  Average accessible places per population center: {avg_accessibility:.1f}"
    )
    logger.info(
        f"  Range: {min_accessibility} to {max_accessibility} accessible places"
    )
    logger.info(
        f"  {sum(1 for x in accessibility_counts if x == 1)} centers have only 1 accessible place (service deserts)"
    )
    logger.info(
        f"  {sum(1 for x in accessibility_counts if x >= 5)} centers have 5+ accessible places (well-served areas)"
    )

    # Compute population effective purchasing power using accessibility-weighted demographics
    # Implements spatial equity theory: divides population by service availability
    # Areas with fewer accessible services get higher population effective purchasing power weights
    #! Compute population effective purchasing power
    #! The effective market value of a population center
    if weights is None:
        origins["population_purchasing_power"] = (
            origins["population"] / origins["number_of_accessibile_markets"]
        )
        logger.info("Using simple accessibility weighting (no income data)")
    else:
        # Handle NaN values in income data
        income_values = weights["income"].values.copy()

        logger.info(f"STEP 1 - Original income sample: {income_values[:5]}")
        logger.info(
            f"STEP 1 - Original income NaN count: {np.isnan(income_values).sum()}"
        )

        income_values = weights["income"].values.copy()  # Make a copy
        logger.info(f"STEP 2 - Copied income sample: {income_values[:5]}")

        # Log income data quality
        nan_count = np.isnan(income_values).sum()
        valid_count = len(income_values) - nan_count
        logger.info(
            f"STEP 3 - Income data quality: {valid_count}/{len(income_values)} valid values, {nan_count} NaN values"
        )
        if nan_count > 0:
            median_income = np.nanmedian(income_values)
            logger.info(f"STEP 4 - Calculated median income: SAR{median_income:,.0f}")
            if np.isnan(median_income):
                logger.warning("All income values are NaN, using neutral weight of 1.0")
                income_values = np.ones_like(income_values)
            else:
                logger.info(
                    f"STEP 5 - Replacing {nan_count} NaN income values with median: SAR{median_income:,.0f}"
                )
                # CRITICAL: Use the CORRECTED income_values, not the original
                income_values = np.nan_to_num(income_values, nan=median_income)
                logger.info(
                    f"STEP 6 - After np.nan_to_num, income sample: {income_values[:5]}"
                )
                logger.info(
                    f"STEP 6 - After np.nan_to_num, NaN count: {np.isnan(income_values).sum()}"
                )

        # Check alignment
        if len(income_values) != len(origins):
            income_values = income_values[: len(origins)]

        # Calculate purchasing power
        population_values = origins["population"].values
        accessibility_values = origins["number_of_accessibile_markets"].values

        origins["population_purchasing_power"] = (
            population_values * income_values / accessibility_values
        )

    total_population_purchasing_power = origins["population_purchasing_power"].sum()
    logger.info(
        f"Total market value without considering accessibility: {total_population_purchasing_power:,.0f}"
    )
    # Calculate market potential for each destination (place/facility)
    # Implements gravity model theory: sum of accessible population effective purchasing powers
    # Each destination's market size = sum of all populations that can reach it
    market = {k: [] for k in range(matrix.shape[1])}
    logger.info("Calculating market potential for each destination...")
    logger.info("Market potential calculation (w/o accessibility) diagnostic:")
    logger.info(
        f"  Market potential calculation range: {origins['population_purchasing_power'].min():.2f} to {origins['population_purchasing_power'].max():.2f}"
    )
    logger.info(
        f"  Market potential NaN count: {origins['population_purchasing_power'].isna().sum()}"
    )
    for i in range(matrix.shape[1]):
        for k, v in od_cost_matrix.items():
            if i in v:
                market[i].append(origins["population_purchasing_power"].iloc[k])

    # Aggregate market potential for each destination
    # Sum all population effective purchasing powers that can access each destination
    # Results in total market size/customer base for each facility
    # Example: Downtown supermarket might have 25,000 total potential customers, suburban one has 8,500
    destinations["market"] = [sum(v) for v in market.values()]
    logger.info("Market calculation results:")
    logger.info(f"  Market values sample: {destinations['market'][:5]}")
    logger.info(f"  Market NaN count: {sum(np.isnan(destinations['market']))}")
    logger.info(f"  Market zero count: {sum(np.array(destinations['market']) == 0)}")
    logger.info(f"  Non-zero market count: {sum(np.array(destinations['market']) > 0)}")

    # ===== INSERT ENHANCED MARKET CALCULATION DEBUGGING HERE =====
    logger.info("=== MARKET CALCULATION DEBUG ===")
    logger.info(
        f"Total origins with valid market potential: {sum(~np.isnan(origins['population_purchasing_power']))}"
    )
    logger.info(
        f"Total origins with zero market potential: {sum(origins['population_purchasing_power'] == 0)}"
    )

    # Check each destination's market calculation
    for i in range(min(5, len(destinations))):
        dest_market_contributors = market[i]
        logger.info(f"Destination {i} market calculation:")
        logger.info(
            f"  Number of contributing origins: {len(dest_market_contributors)}"
        )
        if len(dest_market_contributors) > 0:
            logger.info(f"  Contributors sample: {dest_market_contributors[:3]}")
            logger.info(f"  Contributors sum: {sum(dest_market_contributors)}")
            logger.info(
                f"  Any NaN contributors: {any(np.isnan(dest_market_contributors))}"
            )
        else:
            logger.info("  No origins can access this destination")

    # Check accessibility matrix
    accessible_destinations_per_origin = [len(v) for v in od_cost_matrix.values()]
    logger.info(
        f"Origins with 0 accessible destinations: {sum(x == 0 for x in accessible_destinations_per_origin)}"
    )
    logger.info(
        f"Total accessible origin-destination pairs: {sum(accessible_destinations_per_origin)}"
    )
    logger.info("=== END MARKET CALCULATION DEBUG ===")
    # ===== END ENHANCED MARKET CALCULATION DEBUGGING =====

    market_stats = destinations["market"]
    destinations["market"] = [sum(v) for v in market.values()]

    logger.info("Market potential calculated:")
    logger.info(
        f"  Average market size per destination: {np.mean(market_stats):,.0f} potential market value"
    )
    logger.info(
        f"  Range: {np.min(market_stats):,.0f} to {np.max(market_stats):,.0f} potential market value"
    )
    logger.info(
        f"  Total market value across all destinations: {np.sum(market_stats):,.0f}"
    )

    # Create spatial tessellation grid for aggregation analysis
    # Uses adaptive grid sizing based on population density
    # Create spatial tessellation grid for aggregation analysis
    grid = create_grid(origins, grid_size=None)

    # Perform spatial joins to assign data points to grid cells
    origins = origins.to_crs(grid.crs)
    origins.geometry = origins.geometry.centroid

    poulation_grid = gpd.sjoin(origins, grid, how="left", predicate="intersects")
    places_grid = gpd.sjoin(destinations, grid, how="left", predicate="within")

    # Aggregate spatial data at grid cell level
    data = pd.concat(
        [
            grid,
            poulation_grid.groupby("index_right")["population"]
            .sum()
            .rename("number_of_persons"),
            poulation_grid.groupby("index_right")["population_purchasing_power"]
            .sum()
            .rename("population_purchasing_power"),
            places_grid.groupby("index_right")["geometry"]
            .count()
            .rename("number_of_supermarkets"),
            #! Total market potential from all population centers that can reach facilities in this grid
            places_grid.groupby("index_right")["market"]
            .sum()
            .rename("population_purchasing_potential"),
        ],
        axis=1,
    )

    # Data cleaning: remove empty grid cells
    mask = ~data.iloc[:, 1:].isna().all(axis=1)
    data = data.loc[mask].fillna(0.0).reset_index(drop=True)

    logger.info(f"Created {len(data)} grid cells with data")

    return data


def create_territory_boundaries(
    masked_grided_data: gpd.GeoDataFrame,
    req: ReqClustersForSalesManData,
    groups: dict,
) -> Tuple[gpd.GeoDataFrame, dict]:
    """
    Create territory boundaries from clustered grid data using convex hull method

    Args:
        masked_grided_data: The clustered grid data
        req: The request object with num_sales_man
        groups: Dictionary mapping group_id to list of grid cell indices

    Returns:
        Tuple of (boundaries_gdf, boundaries_geojson_dict)
    """

    logger.info("Creating territory boundaries using convex hull method...")

    # Aggregate data by group
    aggregated_output = masked_grided_data.groupby("group", observed=False).agg(
        {
            "number_of_persons": "sum",
            "population_purchasing_power": "sum",
            "number_of_supermarkets": "sum",
            "population_purchasing_potential": "sum",
        }
    )

    logger.info(f"Aggregated data for {len(aggregated_output)} groups")

    # Create boundaries list
    boundaries = []
    for group in masked_grided_data.group.unique():
        if pd.isna(group):
            continue

        # Get territory data for this group
        territory_data = masked_grided_data.loc[masked_grided_data.group == group]

        # Create convex hull boundary
        geometry = territory_data.geometry.union_all().convex_hull

        boundaries.append({"group": group, "geometry": geometry})

    # Convert to DataFrame and merge with aggregated data
    boundaries_df = pd.DataFrame(boundaries)
    boundaries_df = boundaries_df.merge(aggregated_output, on="group", how="left")
    boundaries_gdf = gpd.GeoDataFrame(boundaries_df)

    logger.info(f"Created {len(boundaries_gdf)} territory boundaries")

    # Handle overlapping geometries
    for i in range(len(boundaries_gdf)):
        current_geom = boundaries_gdf.iloc[i].geometry
        for j in range(i):
            if j < len(boundaries_gdf):
                prev_geom = boundaries_gdf.iloc[j].geometry
                try:
                    current_geom = current_geom.difference(prev_geom)
                except Exception as e:
                    logger.warning(f"Could not subtract territory {j} from {i}: {e}")

        boundaries_gdf.iloc[i, boundaries_gdf.columns.get_loc("geometry")] = (
            current_geom
        )

    # Create GeoJSON representation
    logger.info("Applied difference operations to prevent boundary overlaps")

    boundaries_geojson = {"type": "FeatureCollection", "features": []}

    for idx, row in boundaries_gdf.iterrows():
        feature = {
            "type": "Feature",
            "properties": {
                "group": int(row["group"]) if not pd.isna(row["group"]) else None,
                "number_of_persons": (
                    int(row["number_of_persons"])
                    if not pd.isna(row["number_of_persons"])
                    else 0
                ),
                "population_purchasing_power": (
                    float(row["population_purchasing_power"])
                    if not pd.isna(row["population_purchasing_power"])
                    else 0
                ),
                "number_of_supermarkets": (
                    int(row["number_of_supermarkets"])
                    if not pd.isna(row["number_of_supermarkets"])
                    else 0
                ),
                "population_purchasing_potential": (
                    float(row["population_purchasing_potential"])
                    if not pd.isna(row["population_purchasing_potential"])
                    else 0
                ),
            },
            "geometry": row["geometry"].__geo_interface__,
        }
        boundaries_geojson["features"].append(feature)
    logger.info("Created GeoJSON representation of territory boundaries")

    return boundaries_gdf, boundaries_geojson


def select_nbrs_with_sum(
    i: int, cost: np.ndarray, max_share: float, shares: dict, used: list[int]
) -> list[int]:
    """
    A helper function for clustering funtionality. It makes sure that the cluster are formed by neighboring
    gridcells and calculates the sum of indicator value for each itteration.

    args:
    ----
    `i` is index of the origin
    `cost` is od distnace matrix
    `max_share` is the max share of the indicator each cluster can have
    `shares` is the assigned value to each destination
    `used` is the a list of gridcells that are taken

    return:
    ------
    a list of neighboring gridcells for origin i that will become of cluster
    """
    logger.debug(f"Building cluster starting from grid cell {i}")
    logger.debug(
        f"Target max share: {max_share:,.0f}, Available unused cells: {len(cost) - len(used)}"
    )

    # Sort grid cells by distance from origin i (nearest neighbor ordering)
    # Implements spatial contiguity constraint for cluster formation
    # Ensures clusters are geographically compact rather than spatially fragmented
    # Example: From grid cell 45, sorted neighbors might be [46, 44, 55, 35, 47, 43, 56, 34...]
    x = np.argsort(cost)  # Returns indices sorted by ascending distance

    logger.debug(f"Sorted {len(x)} neighbors by distance from seed cell {i}")

    # Initialize accumulator variables
    value = 0
    nbrs = []

    added_cells = []
    skipped_cells = []

    # Greedy nearest-neighbor selection with capacity constraint
    for idx, cell_idx in enumerate(x):
        # Skip grid cells already assigned to other clusters
        if cell_idx in used:
            continue

        # Add current grid cell's indicator value to cluster total
        cell_value = shares[cell_idx]
        value += cell_value
        nbrs.append(cell_idx)

        # Check if cluster has reached target capacity
        if value >= max_share:
            logger.debug(
                f"  Cluster reached target capacity ({value:,.0f} >= {max_share:,.0f})"
            )
            break
    # Determine which cells were never considered (after the break or beyond capacity)
    all_cells = set(x)  # All cells sorted by distance
    considered_cells = set(added_cells + skipped_cells)
    never_used_cells = all_cells - considered_cells

    # Log comprehensive cell usage statistics
    logger.info(
        f"Cluster built from seed {i}: {len(nbrs)} cells, {value:,.0f} total market value"
    )
    logger.info(f"  Load balancing: {100*value/max_share:.1f}% of target capacity")
    logger.info(f"  Added cells: {added_cells}")
    logger.info(f"  Skipped cells (already used): {skipped_cells}")
    logger.info(f"  Never considered cells: {list(never_used_cells)}")
    logger.info(
        f"  Cell usage summary: {len(added_cells)} added, {len(skipped_cells)} skipped, {len(never_used_cells)} never considered"
    )
    return nbrs


def plot_results(
    grided_data: gpd.GeoDataFrame,
    columns: list[str],
    n_cols: int,
    n_rows: int,
    colors: list[str],
    alpha: float = 0.8,
    show_legends: bool = True,
    edge_color: str = "white",
    show_title: bool = True,
    subplot_size: tuple = (8, 8),
    title=None,
    save_to_file: bool = False,
    filename: Optional[str] = None,
    static_dir: str = "static/plots",
) -> Optional[str]:
    """
    Enhanced to optionally save plot as file and return URL path
    """
    grid = grided_data.copy(deep=True)
    single_fig_width, single_fig_height = subplot_size

    fig = plt.figure(
        figsize=(
            single_fig_width * n_cols + n_cols,
            single_fig_height * n_rows + n_rows,
        )
    )

    for i, column in enumerate(columns, 1):
        ax = plt.subplot(n_rows, n_cols, i)
        grid.set_crs(epsg=4326, inplace=True)
        grid.to_crs(epsg=3857).plot(
            column=f"{column}",
            legend=show_legends,
            cmap=colors[i - 1],
            edgecolor=edge_color,
            linewidth=0.1,
            alpha=alpha,
            ax=ax,
        )
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
        ax.axis("off")
        if show_title:
            if title is not None:
                if len(title) == len(columns):
                    ax.set_title(title[i - 1], fontsize=10, pad=10)

    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(top=0.85, hspace=0.3, wspace=0.2)

    if save_to_file:
        # Create directory if it doesn't exist
        os.makedirs(static_dir, exist_ok=True)

        # Generate unique filename
        if filename is None:
            filename = f"plot_{uuid.uuid4().hex[:8]}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{timestamp}_{filename}.png"
        filepath = os.path.join(static_dir, full_filename)

        # Save the plot
        plt.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        # Return URL path that FastAPI can serve
        return f"/static/plots/{full_filename}"
    else:
        plt.show()
        plt.close(fig)
        return None


def plot_facilities_with_territories(places, boundaries_gdf, request_id):
    """Show actual facility locations with territory assignments"""

    fig, ax = plt.subplots(figsize=(12, 10))

    # Background: Territory boundaries
    boundaries_gdf.plot(
        column="group",
        cmap="Pastel1",
        alpha=0.4,
        edgecolor="black",
        linewidth=1,
        ax=ax,
        legend=False,
    )

    # Foreground: Facility points (no legend to avoid conflicts)
    places.plot(
        column="group",
        cmap="tab10",
        marker="o",
        markersize=60,
        edgecolor="black",
        linewidth=1,
        alpha=0.9,
        ax=ax,
        legend=False,  # Set to False to avoid the error
    )

    # Add title with facility count info
    ax.set_title(
        f"Supermarket Locations by Sales Territory\n" f"",
        fontsize=14,
        fontweight="bold",
    )
    ax.axis("off")

    # Save the plot
    if request_id:
        os.makedirs("static/plots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{request_id}_facilities_with_territories.png"
        filepath = os.path.join("static/plots", filename)
        plt.savefig(filepath, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        return f"/static/plots/{filename}"

    return None


def generate_all_plots(
    masked_grided_data: gpd.GeoDataFrame,
    places: gpd.GeoDataFrame,
    boundaries_gdf: gpd.GeoDataFrame = None,
    request_id: str = None,
) -> dict:
    """
    Generate all plots and save them as static files
    """
    if request_id is None:
        request_id = uuid.uuid4().hex[:8]

    plots = {}

    # Cluster of markets plot
    plots["cluster_markets"] = plot_results(
        places,
        ["group"],
        1,
        1,
        ["tab20c"],
        alpha=1,
        show_legends=False,
        edge_color=None,
        show_title=True,
        title=["Cluster of markets"],
        save_to_file=True,
        filename=f"{request_id}_cluster_markets",
    )

    # Territory boundaries plot
    if boundaries_gdf is not None and len(boundaries_gdf) > 0:
        import matplotlib.pyplot as plt

        n_territories = len(boundaries_gdf)
        plots["territory_boundaries"] = plot_results(
            boundaries_gdf[["geometry", "group"]],
            ["group"],
            1,
            1,
            [plt.get_cmap("jet", n_territories)],
            alpha=1,
            show_legends=True,
            edge_color=None,
            show_title=True,
            title=["Territory Boundaries"],
            save_to_file=True,
            filename=f"{request_id}_territory_boundaries",
        )
    if boundaries_gdf is not None and len(boundaries_gdf) > 0:
        plots["facilities_with_territories"] = plot_facilities_with_territories(
            places, boundaries_gdf, request_id
        )

    # Individual metric plots
    metrics = [
        ("number_of_persons", "Greens", "Number of persons"),
        (
            "population_purchasing_power",
            "Reds",
            "population effective purchasing power",
        ),
        ("number_of_supermarkets", "Blues", "Number of supermarkets"),
        (
            "population_purchasing_potential",
            "Purples",
            "population purchasing potential",
        ),
    ]

    for column, color, title in metrics:
        plot_key = column.replace("_", "-")
        plots[plot_key] = plot_results(
            masked_grided_data,
            [column],
            1,
            1,
            [color],
            alpha=1,
            show_legends=True,
            edge_color=None,
            show_title=True,
            title=[title],
            save_to_file=True,
            filename=f"{request_id}_{column}",
        )

    return plots


async def get_clusters_for_sales_man(
    req: ReqClustersForSalesManData,
) -> dict[any, any]:
    """
    Main funtion to produce the clusters for the salesman problem

    Returns a geodataframe containing gridcells (polygons) under geometry column
    each grid cell is classified by cluster index under group column
    """
    # req = {
    #     "city_name": "Riyadh",
    #     "country_name": "Saudi Arabia",
    #     "user_id": "test_user",
    #     "boolean_query": "supermarket",
    #     "num_sales_man": 4,
    #     "distance_limit": 5,
    #     "include_raw_data": True
    # }

    # from types import SimpleNamespace
    # req = SimpleNamespace(**req)

    default_zoom = 14

    logger.info(
        f"Starting sales territory clustering for {req.city_name}, {req.country_name}"
    )
    logger.info(f"Target number of sales territories: {req.num_sales_man}")
    logger.info(f"Distance limit: {req.distance_limit}km, Zoom level: {default_zoom}")

    # Retrieve geographic boundary data for specified city
    all_cities = await fetch_country_city_data()

    # Search for target city within country's city database
    found_city = None
    for city in all_cities.get(req.country_name, []):
        if city["name"] == req.city_name:
            found_city = city
            break

    if found_city is None:
        logger.error(f"City {req.city_name} not found in {req.country_name}")
        raise ValueError(f"City not found: {req.city_name}")

    # Extract bounding box coordinates
    bounding_box = found_city.get("bounding_box", [])
    logger.info(f"City bounding box: {len(bounding_box)} coordinate pairs")

    # Load demographic and economic data for the study area
    # Zoom level controls resolution/granularity of population data
    logger.info("Loading population and income data...")
    population_gdf, income_gdf = await get_population_and_income(
        bounding_box, zoom_level=default_zoom
    )
    logger.info(f"Loaded {len(population_gdf)} population records")
    logger.info(f"Loaded {len(income_gdf)} income records")
    if income_gdf is not None and len(income_gdf) > 0:
        logger.info("Income data diagnostic:")
        for col in income_gdf.columns:
            if col != "geometry":
                values = income_gdf[col].values
                logger.info(
                    f"  Column '{col}': {len(values)} values, {np.isnan(values).sum()} NaN"
                )
                if not np.all(np.isnan(values)):
                    logger.info(
                        f"    Range: {np.nanmin(values):.2f} to {np.nanmax(values):.2f}"
                    )
    else:
        logger.warning("Income data is empty or None")

    # Retrieve and filter businesses/facilities data
    logger.info("Loading business/facility data...")
    page_token = ""
    data_load_req = ReqFetchDataset(
        boolean_query=req.boolean_query,
        action="full data",
        page_token=page_token,
        city_name=req.city_name,
        country_name=req.country_name,
        user_id=req.user_id,
        full_load=True,
    )

    places = await fetch_dataset(data_load_req)
    places = filter_data_by_bounding_box(places, bounding_box)
    logger.info(f"Filtered to {len(places)} places within study area")

    # Remove duplicate facility locations

    original_count = len(places)
    places = places.loc[places.geometry.drop_duplicates().index]
    logger.info(f"Processing+++ {len(places)} unique places")
    logger.info(
        f"Removed {original_count - len(places)} duplicate locations, {len(places)} unique places remain"
    )

    # Generate grid-based spatial aggregation with accessibility analysis
    # Implements spatial tessellation with market potential calculation
    # Combines population, facilities, income, and accessibility into unified spatial framework
    logger.info("Generating grid-based spatial aggregation...")
    grided_data = get_grids_of_data(
        population_gdf, places, income_gdf, req.distance_limit
    )

    # Filter to grid cells with actual market potential
    mask = (grided_data["number_of_persons"] > 0) | (
        grided_data["population_purchasing_potential"] > 0
    )
    masked_grided_data = grided_data[mask].reset_index(drop=True)

    if len(masked_grided_data) == 0:
        logger.error("No grid cells with market potential found!")
        raise ValueError("No viable grid cells for territory division")

    # Calculate geometric centroids for distance calculations
    centroids = masked_grided_data.geometry.map(shapely.centroid)
    nbrs = centroids.to_frame()
    nbrs["longitude"] = nbrs.geometry.x
    nbrs["latitude"] = nbrs.geometry.y

    logger.info(f"Calculated centroids for {len(nbrs)} grid cells")
    # Compute distance matrix between all grid cell centroids
    logger.info("Computing distance matrix between grid centroids...")

    matrix = haversine(
        nbrs.latitude.values,
        nbrs.longitude.values,
        nbrs.latitude.values,
        nbrs.longitude.values,
    )

    # Calculate target market share per salesperson
    total_purchasing_power = masked_grided_data["population_purchasing_potential"].sum()
    equitable_share = total_purchasing_power / req.num_sales_man

    logger.info(f"Total market value:+++ {total_purchasing_power:,.0f}")
    logger.info(f"Target per territory+++: {equitable_share:,.0f}")
    logger.info("Market distribution analysis:")
    logger.info(f"  Total market value: {total_purchasing_power:,.0f}")
    logger.info(f"  Target market value per territory: {equitable_share:,.0f}")
    logger.info(
        f"  This represents balanced workload distribution across {req.num_sales_man} salespeople"
    )

    # Initialize clustering data structures
    used = []
    groups = {i: [] for i in range(req.num_sales_man)}

    # Greedy spatial clustering algorithm
    j = 0
    clusters_created = 0

    for i in range(masked_grided_data.shape[0]):
        if i in used:
            continue
        else:
            logger.info(f"Creating cluster {j} starting from grid cell {i}")

            # Find spatially contiguous neighbors within capacity limit
            # Find spatially contiguous neighbors within capacity limit
            # Implements greedy nearest-neighbor expansion with load balancing
            # Example: Starting from grid 25, might select [25, 26, 35, 24, 36, 15] totaling 23,100 customers
            nbrs = select_nbrs_with_sum(
                i,
                matrix[i],
                equitable_share,
                masked_grided_data["population_purchasing_potential"].values,
                used,
            )

            # Assign selected neighbors to current cluster
            groups[j].extend(nbrs)
            used.extend(nbrs)

            cluster_customers = sum(
                masked_grided_data["population_purchasing_potential"].iloc[idx]
                for idx in nbrs
            )
            logger.info(
                f"Cluster {j} completed: {len(nbrs)} cells, {cluster_customers:,.0f} market value"
            )
            j += 1
            clusters_created += 1

        # Stop when all requested clusters are created
        if j >= req.num_sales_man:
            logger.info(f"Reached target number of clusters ({req.num_sales_man})")
            break

    logger.info("Clustering completed:")
    logger.info(f"  Clusters created: {clusters_created}")
    logger.info(
        f"  Grid cells assigned: {len(used)}/{len(masked_grided_data)} ({100*len(used)/len(masked_grided_data):.1f}%)"
    )
    logger.info(f"  Unassigned cells: {len(masked_grided_data) - len(used)}")

    # Helper function to map grid cell indices to cluster labels
    def return_group_number(index: int) -> int:
        """
        Returns back the class/group index for each grid cell based in the `groups` dict
        `groups` is the dict created in the `get_clusters_for_sales_man`
        `index`is the index of the gridcell in the `masked_grided_data`
        """
        for k, v in groups.items():
            if index in v:
                return k
        return None

    # Apply cluster labels to grid data
    masked_grided_data = masked_grided_data.assign(group=lambda x: x.index)
    masked_grided_data["group"] = masked_grided_data["group"].map(return_group_number)

    cluster_stats = (
        masked_grided_data.groupby("group")
        .agg({"population_purchasing_potential": ["sum", "count"]})
        .round(0)
    )
    logger.info("Final cluster statistics:")
    for group_id in range(req.num_sales_man):
        if group_id in groups:
            cells = len(groups[group_id])
            customers = masked_grided_data[masked_grided_data["group"] == group_id][
                "population_purchasing_potential"
            ].sum()
            logger.info(
                f"  Cluster {group_id}: {cells} cells, {customers:,.0f} market value ({100*customers/total_purchasing_power:.1f}% of total)"
            )

    unassigned = len(masked_grided_data[masked_grided_data["group"].isna()])
    if unassigned > 0:
        logger.warning(f"  {unassigned} cells remain unassigned")
    logger.info("Sales territory clustering completed successfully")
    # Create a GeoDataFrame for places with group assignments
    # logger.info("saving file")
    # masked_grided_data.to_file("sales_territories.geojson", driver="GeoJSON")
    # places.to_file("places.geojson", driver="GeoJSON")
    places["group"] = -1
    for i in masked_grided_data.group.unique():
        cluster = (
            masked_grided_data.loc[masked_grided_data.group == i]
            .union_all()
            .convex_hull
        )
        places.loc[places.geometry.within(cluster), "group"] = i

    # Generate unique request ID
    request_id = uuid.uuid4().hex[:8]
    logger.info(f"Generating plots for request {request_id}")

    # Create territory boundaries
    boundaries_gdf, boundaries_geojson = create_territory_boundaries(
        masked_grided_data, req, groups
    )

    # Generate plots and get their URLs

    logger.info("Creating territory boundaries...")

    plot_urls = generate_all_plots(
        masked_grided_data, places, boundaries_gdf=boundaries_gdf, request_id=request_id
    )

    # Generate territory-level analytics
    logger.info("Sales territory clustering and plot generation completed successfully")
    territory_analytics = []
    territory_boundaries = []

    for group_id in range(req.num_sales_man):
        if group_id in groups:
            # Extract territory data
            territory_data = masked_grided_data[masked_grided_data["group"] == group_id]

            # Calculate comprehensive territory metrics
            territory_stats = {
                "territory_id": group_id,
                "grid_cells": len(groups[group_id]),
                "total_population": int(territory_data["number_of_persons"].sum()),
                "population_purchasing_power": round(
                    territory_data["population_purchasing_power"].sum(), 2
                ),
                "facility_count": int(territory_data["number_of_supermarkets"].sum()),
                "population_purchasing_potential": int(
                    territory_data["population_purchasing_potential"].sum()
                ),
                "market_share_percentage": round(
                    (
                        territory_data["population_purchasing_potential"].sum()
                        / total_purchasing_power
                    )
                    * 100,
                    1,
                ),
                "avg_market_value_per_grid_cell_SAR": round(
                    territory_data["population_purchasing_power"].mean(), 2
                ),
                "avg_population_per_grid_cell": round(
                    territory_data["number_of_persons"].sum() / len(groups[group_id]),
                    0,
                ),
                "avg_facilities_per_grid_cell": round(
                    territory_data["number_of_supermarkets"].sum()
                    / len(groups[group_id]),
                    2,
                ),
            }
            territory_analytics.append(territory_stats)

            # Create territory boundary geometry
            territory_boundary = {
                "territory_id": group_id,
                "boundary_geometry": territory_data.union_all().convex_hull.__geo_interface__,
                "centroid": territory_data.geometry.to_crs(epsg=3857)
                .centroid.to_crs(territory_data.geometry.crs)
                .union_all()
                .__geo_interface__,
                "area_km2": round(
                    territory_data.union_all().area * 111.32**2, 2
                ),  # Convert to km²
            }
            territory_boundaries.append(territory_boundary)

    # Generate business intelligence insights
    total_population = sum(t["total_population"] for t in territory_analytics)
    total_facilities = sum(t["facility_count"] for t in territory_analytics)
    print(f"Territory analytics: {territory_analytics}")
    total_facilities = sum(t["facility_count"] for t in territory_analytics)
    # Market balance analysis
    customer_variance = np.var(
        [t["population_purchasing_power"] for t in territory_analytics]
    )
    population_variance = np.var([t["total_population"] for t in territory_analytics])

    business_insights = {
        "market_balance_score": round(
            100
            - (customer_variance / (total_purchasing_power / req.num_sales_man) * 100),
            1,
        ),
        "population_distribution_score": round(
            100 - (population_variance / (total_population / req.num_sales_man) * 100),
            1,
        ),
        "avg_customers_purchasing_power_per_territory": round(
            total_purchasing_power / req.num_sales_man, 0
        ),
        "avg_facilities_per_territory": round(total_facilities / req.num_sales_man, 1),
        "territory_efficiency_ratio": round(
            total_purchasing_power / total_facilities, 1
        ),
        "accessibility_analysis": {
            "high_accessibility_territories": len(
                [
                    t
                    for t in territory_analytics
                    if t["avg_market_value_per_grid_cell_SAR"]
                    > np.mean(
                        [
                            t["avg_market_value_per_grid_cell_SAR"]
                            for t in territory_analytics
                        ]
                    )
                ]
            ),
            "service_desert_territories": len(
                [
                    t
                    for t in territory_analytics
                    if t["avg_facilities_per_grid_cell"] < 1.0
                ]
            ),
            "well_served_territories": len(
                [
                    t
                    for t in territory_analytics
                    if t["avg_facilities_per_grid_cell"] >= 2.0
                ]
            ),
        },
        "optimization_recommendations": generate_optimization_recommendations(
            territory_analytics, req
        ),
    }

    # Performance metrics for territory comparison
    performance_metrics = {
        "territory_rankings": {
            "highest_potential": max(
                territory_analytics,
                key=lambda t: t["population_purchasing_power"],
            ),
            "most_efficient": max(
                territory_analytics,
                key=lambda t: t["population_purchasing_power"]
                / max(t["facility_count"], 1),
            ),
            "most_accessible": max(
                territory_analytics,
                key=lambda t: t["avg_market_value_per_grid_cell_SAR"],
            ),
            "largest_coverage": max(territory_boundaries, key=lambda t: t["area_km2"]),
        },
        "equity_analysis": {
            "customer_balance": {
                "standard_deviation": round(
                    np.std(
                        [t["population_purchasing_power"] for t in territory_analytics]
                    ),
                    0,
                ),
                "coefficient_variation": round(
                    np.std(
                        [t["population_purchasing_power"] for t in territory_analytics]
                    )
                    / np.mean(
                        [t["population_purchasing_power"] for t in territory_analytics]
                    ),
                    3,
                ),
            },
            "workload_balance": calculate_workload_balance(territory_analytics),
        },
    }
    original_population = population_gdf["Population_Count"].sum()
    grid_population = masked_grided_data["number_of_persons"].sum()
    territory_population = sum(
        territory["total_population"] for territory in territory_analytics
    )

    print(f"Population tracking:")
    print(f"  Original: {original_population:,}")
    print(f"  Grid total: {grid_population:,}")
    print(f"  Territory total: {territory_population:,}")
    print(f"  Discrepancy: {abs(original_population - territory_population):,}")
    # Core response data
    response_data = {
        "success": True,
        "request_id": request_id,
        "plots": plot_urls,
        "metadata": {
            "Population_Count": int(population_gdf["Population_Count"].sum()),
            "total_purchasing_power": int(total_purchasing_power),
            "clusters_created": clusters_created,
            "target_customers_purchasing_power_per_territory": int(equitable_share),
            "purchasing_power_per_territory": int(equitable_share),
            "city_name": req.city_name,
            "country_name": req.country_name,
            "analysis_date": datetime.now().isoformat(),
            "distance_limit_km": req.distance_limit,
            "business_type": req.boolean_query,
        },
        "territory_analytics": territory_analytics,
        "territory_boundaries": territory_boundaries,
        "territory_boundaries_geojson": boundaries_geojson,
        "business_insights": business_insights,
        "performance_metrics": performance_metrics,
    }

    # Geographic summary calculations
    geographic_summary = {
        "total_area_km2": round(sum(t["area_km2"] for t in territory_boundaries), 2),
        "population_density_per_km2": round(
            total_population / sum(t["area_km2"] for t in territory_boundaries),
            1,
        ),
        "facility_density_per_km2": round(
            total_facilities / sum(t["area_km2"] for t in territory_boundaries),
            3,
        ),
    }

    # Raw data (conditional)
    if req.include_raw_data:
        raw_cluster_data = {
            "grid_data_geojson": masked_grided_data.to_json(),
            "places_data_geojson": places.to_json(),
        }
    else:
        raw_cluster_data = None

    # Add remaining fields
    response_data["geographic_summary"] = geographic_summary
    response_data["raw_cluster_data"] = raw_cluster_data

    logger.info("Sales territory analysis completed successfully")

    return response_data


def generate_optimization_recommendations(territory_analytics, req):
    """Generate strategic recommendations based on territory analysis"""
    recommendations = []

    # Analyze territory imbalances
    territory_purchasing_powers = [
        t["population_purchasing_power"] for t in territory_analytics
    ]
    territory_avg_purchasing_power = np.mean(territory_purchasing_powers)

    for territory in territory_analytics:
        if (
            territory["population_purchasing_power"]
            < territory_avg_purchasing_power * 0.85
        ):
            recommendations.append(
                f"Territory {territory['territory_id']}: Consider expanding boundaries - below average market potential"
            )
        elif (
            territory["population_purchasing_power"]
            > territory_avg_purchasing_power * 1.15
        ):
            recommendations.append(
                f"Territory {territory['territory_id']}: Consider subdividing - above average workload"
            )

        if territory["avg_facilities_per_grid_cell"] < 0.5:
            recommendations.append(
                f"Territory {territory['territory_id']}: Service desert - consider additional facilities"
            )

    # Strategic insights
    if len(recommendations) == 0:
        recommendations.append(
            "Territories are well-balanced for equitable sales operations"
        )

    recommendations.append(
        f"Optimal distance limit ({req.distance_limit}km) ensures good accessibility coverage"
    )
    recommendations.append(
        "Regular reassessment recommended as market conditions evolve"
    )

    return recommendations


def calculate_workload_balance(territory_analytics):
    """Calculate workload balance metrics"""
    workloads = [
        t["population_purchasing_power"] / max(t["facility_count"], 1)
        for t in territory_analytics
    ]

    return {
        "avg_customers_per_facility": round(np.mean(workloads), 1),
        "workload_standard_deviation": round(np.std(workloads), 1),
        "most_efficient_territory": min(
            territory_analytics,
            key=lambda t: t["population_purchasing_power"]
            / max(t["facility_count"], 1),
        )["territory_id"],
        "least_efficient_territory": max(
            territory_analytics,
            key=lambda t: t["population_purchasing_power"]
            / max(t["facility_count"], 1),
        )["territory_id"],
    }
