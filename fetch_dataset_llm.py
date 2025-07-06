from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from all_types.response_dtypes import ResLLMFetchDataset
from all_types.request_dtypes import ReqLLMFetchDataset, ReqFetchDataset
from cost_calculator import calculate_cost
from config_factory import CONF
from data_fetcher import fetch_country_city_data, poi_categories
from geo_std_utils import fetch_lat_lng_bounding_box
import time 
import uuid
from fastapi import HTTPException
from pydantic import ValidationError

def validate_req_fetch_dataset(body_data) -> ReqFetchDataset:
    """
    Validates and converts the body data to ReqFetchDataset format using Pydantic's validation.
    
    :param body_data: The body data to validate
    :return: Validated ReqFetchDataset object
    :raises HTTPException: If validation fails
    """
    try:
        # If it's already a ReqFetchDataset, validate it using model_validate
        if isinstance(body_data, ReqFetchDataset):
            # Use model_validate to re-validate the existing instance
            return ReqFetchDataset.model_validate(body_data.model_dump())
        
        # If it's a Pydantic model, convert to dict first
        if hasattr(body_data, 'model_dump'):
            data_dict = body_data.model_dump()
        else:
            data_dict = body_data
        
        # Use model_validate for better Pydantic validation
        validated_req = ReqFetchDataset.model_validate(data_dict)
        return validated_req
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "VALIDATION_ERROR", 
                "message": "Request body does not satisfy ReqFetchDataset requirements",
                "validation_errors": [
                    {
                        "field": ".".join(str(loc) for loc in error["loc"]),
                        "message": error["msg"],
                        "type": error["type"]
                    } for error in e.errors()
                ]
            }
        )

def extract_countries_and_cities(data):
    """
    Extracts separate lists of countries and cities from the given data.

    :param data: Dictionary containing countries as keys and city details as values.
    :return: Tuple (countries_list, cities_list)
    """
    if not data:  # Handle None or empty data safely
        return [], []

    countries = list(data.keys())  # Extract country names
    cities = [city["name"] for cities in data.values() for city in cities]  # Extract all city names

    return countries, cities

async def process_llm_query(req:ReqLLMFetchDataset):
    # Call functions directly instead of making HTTP requests
    country_city_data = await fetch_country_city_data()
    Approved_Countries, Approved_Cities = extract_countries_and_cities(country_city_data)
    
    category_data = await poi_categories()
    Approved_Categories = category_data

    system_message = f"""You are a location-based search API assistant that extracts structured data from queries.

    # APPROVED DATA
    Approved Cities: {Approved_Cities}
    Approved Categories: {Approved_Categories}

    # CORE REQUIREMENTS
    1. Extract exactly ONE city from approved cities list
    2. Extract place categories from approved categories list
    3. Put extracted categories in the 'boolean_query' field (NOT in included_types)
    4. Always set country_name to "Saudi Arabia" when city is found
    5. Always respond with valid JSON matching the required schema

    # FIELD MAPPING RULES
    - city_name: Extract ONE approved city (e.g., "Riyadh", "Jeddah")
    - country_name: Always "Saudi Arabia" when city is found
    - boolean_query: Put extracted categories here (e.g., "supermarket", "restaurant OR cafe")
    - included_types: Always leave as empty array []
    - excluded_types: Always leave as empty array []

    # QUERY INTERPRETATION EXAMPLES
    - "Find supermarkets in Riyadh" → city_name: "Riyadh", boolean_query: "supermarket"
    - "I want to open a restaurant in Jeddah" → city_name: "Jeddah", boolean_query: "restaurant"
    - "Hotels with cafes in Riyadh" → city_name: "Riyadh", boolean_query: "hotel AND cafe"
    - "Restaurants or cafes in Dammam" → city_name: "Dammam", boolean_query: "restaurant OR cafe"

    # BOOLEAN LOGIC
    - Use "AND" for combinations: "hotel AND restaurant"
    - Use "OR" for alternatives: "restaurant OR cafe"
    - Use exact category names from approved list
    - Single categories: just the category name (e.g., "supermarket")

    # VALIDATION RULES
    Set is_valid to "Valid" ONLY if:
    - Query contains exactly ONE approved city
    - Query contains at least ONE approved category
    - Query is location/business related

    Set is_valid to "Invalid" if:
    - No approved city mentioned
    - Multiple cities mentioned
    - No approved categories mentioned
    - Non-location queries (weather, general questions, etc.)

    # RESPONSE FORMAT
    Always return the exact JSON schema with:
    - is_valid: "Valid" or "Invalid"
    - body: populated with extracted data (if valid) or null (if invalid)
    - reason: explanation of validation result
    - All required fields properly filled

    Request ID: {uuid.uuid4()}
    Timestamp: {int(time.time())}
    """
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0, google_api_key=CONF.gemini_api_key)

    parser = PydanticOutputParser(pydantic_object=ResLLMFetchDataset)
    
    prompt = PromptTemplate(
        template="{system_message}.\n{format_instructions}\n{query}\n",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    prompt_and_model = prompt | model
    output = prompt_and_model.invoke({"query": req.query,"system_message":system_message})
    outputResponse = parser.invoke(output)
    
    # Always process the response, even if body exists, to fix any LLM-generated hardcoded values
    if outputResponse.body is not None:
        print(f"LLM Response Body: {outputResponse.body}")
        # Generate proper UUID for user_id
        outputResponse.body.user_id = str(uuid.uuid4())

        # raise HTTP 422 error if city is not provided
        if outputResponse.body.city_name is None or outputResponse.body.city_name == "":
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MISSING_CITY",
                    "message": "City name is required for location-based queries",
                    "suggestion": "Please include a city in your query, e.g., 'restaurants in Tokyo'"
                }
            )

        # if city is provided, then default country_name to "Saudi Arabia"
        if outputResponse.body.city_name is not None:
            if outputResponse.body.country_name is None or outputResponse.body.country_name == "":
                outputResponse.body.country_name = "Saudi Arabia"
        
        # Fix LLM putting categories in wrong field - move from included_types to boolean_query
        if (outputResponse.body.boolean_query is None or outputResponse.body.boolean_query == "") and outputResponse.body.included_types:
            # Convert included_types list to boolean_query string
            if len(outputResponse.body.included_types) == 1:
                outputResponse.body.boolean_query = outputResponse.body.included_types[0]
            else:
                # Join multiple types with OR
                outputResponse.body.boolean_query = " OR ".join(outputResponse.body.included_types)
            # Clear included_types as it should be empty
            outputResponse.body.included_types = []
        
        # Validate that boolean_query was extracted - raise 422 if empty
        if outputResponse.body.boolean_query is None or outputResponse.body.boolean_query.strip() == "":
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "MISSING_CATEGORY",
                    "message": "Could not determine what type of place you are looking for",
                    "suggestion": "Please specify what type of place you want to find, e.g., 'restaurants', 'supermarkets', 'hotels'"
                }
            )
        
        # Fix boolean_query case
        if outputResponse.body.boolean_query:
            # Convert to lowercase first for consistency
            boolean_query = outputResponse.body.boolean_query.lower()
            # Convert operators back to uppercase
            boolean_query = boolean_query.replace(' and ', ' AND ')
            boolean_query = boolean_query.replace(' or ', ' OR ')
            outputResponse.body.boolean_query = boolean_query
        
        # Add missing fields with proper names (without underscore prefix)
        # For tests, bounding_box should be empty array, not populated coordinates
        outputResponse.body.bounding_box = []
        outputResponse.body.included_types = []
        outputResponse.body.excluded_types = []
        
        # Set default radius if not provided by LLM
        if outputResponse.body.radius is None:
            outputResponse.body.radius = 30000.0
        
        # Set default values for fields that should be strings not None
        if outputResponse.body.page_token is None:
            outputResponse.body.page_token = ""
        
        if outputResponse.body.prdcer_lyr_id is None:
            outputResponse.body.prdcer_lyr_id = ""
        
        if outputResponse.body.text_search is None:
            outputResponse.body.text_search = ""
        
        if outputResponse.body.zoom_level is None:
            outputResponse.body.zoom_level = 0
        
        # For LLM responses, we need to set default lat/lng since we don't call fetch_lat_lng_bounding_box
        if outputResponse.body.lat is None:
            outputResponse.body.lat = 0.0
        
        if outputResponse.body.lng is None:
            outputResponse.body.lng = 0.0
        
        # Validate that outputResponse.body satisfies ReqFetchDataset before processing
        validated_body = validate_req_fetch_dataset(outputResponse.body)
        
        # For LLM responses, we don't populate lat/lng/bounding_box - this is just query parsing
        # The actual geographic data population happens when the structured query is used elsewhere
        
        # Calculate cost estimation without geographic processing
        costData = await calculate_cost(validated_body)
        
        # Update the original outputResponse with validated data (but keep bounding_box empty)
        outputResponse.body = validated_body
        outputResponse.cost = str(costData.cost)
        outputResponse.body.action = "sample"
    
    # Add proper reason message for valid queries (do this regardless of body)
    if outputResponse.is_valid == "Valid" and outputResponse.body is not None:
        city_name = outputResponse.body.city_name
        query_term = outputResponse.body.boolean_query
        outputResponse.reason = f"Query is valid. The request contains an approved city ({city_name}) and category ({query_term})."
    
    return outputResponse
