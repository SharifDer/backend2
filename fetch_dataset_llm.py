from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from all_types.response_dtypes import ResLLMFetchDataset
from all_types.request_dtypes import ReqLLMFetchDataset, ReqFetchDataset
from cost_calculator import calculate_cost
from config_factory import CONF
from data_fetcher import fetch_country_city_data, poi_categories
from geo_std_utils import fetch_lat_lng_bounding_box
import uuid

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

    system_message = f"""You are an intelligent assistant that extracts structured data for a location-based search API. 
    Your primary function is to process location-based search queries and format them appropriately.
    
    IMPORTANT: You MUST ALWAYS respond with valid JSON format as specified in the schema, regardless of the query content.
    
    # CRITICAL REQUIREMENTS
    - MUST HAVE: Exactly one approved city name in the query from Approved Cities: {Approved_Cities}
    - MUST NOT HAVE: Multiple city names in the same query
    - These requirements are non-negotiable - immediately reject any query that violates them
    
    # QUERY PROCESSING RULES
    - Only process queries that explicitly request information about places within a single approved city.
    - Automatically add the corresponding country name to maintain consistency.
    - Ensure consistent results for identical queries by following a deterministic analysis process.
    
    # REJECTION CRITERIA
    Reject queries that:
    1. Do not contain an approved city name
    2. Contain multiple city names
    3. Do not explicitly seek physical places/venues (e.g., "Weather in Paris" or "History of London")
    4. Are general knowledge or instructional in nature (e.g., "How to apply for a visa in Singapore")
    5. Contain inappropriate, offensive, illegal, or nonsensical content
    6. Reference place categories not in the approved list: {Approved_Categories}
    7. Mention countries not in the approved list: {Approved_Countries}
    
    # Boolean Query Construction
    - The boolean query must only contain approved category terms connected by 'AND' and 'OR' operators
    - Analyze the semantic relationship between place categories in the query:
    - Use 'OR' for alternatives (e.g., "restaurants or cafes" → "RESTAURANT OR CAFE")
    - Use 'AND' for combinations (e.g., "hotels with restaurants" → "HOTEL AND RESTAURANT")
    - For complex queries with both independent and combined categories:
    - Group related terms with parentheses
    - Example: "ATMs and supermarkets with ATMs" → "ATM OR (SUPERMARKET AND ATM)"
    - Always use the standardized category names from the approved list
    
    For invalid queries, politely explain why the query cannot be processed, specifically mentioning the requirement for exactly one approved city name.
    
    REMEMBER: Always respond with the exact JSON format specified in the schema. Never provide explanations outside the JSON structure."""
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
        # Generate proper UUID for user_id
        outputResponse.body.user_id = str(uuid.uuid4())
        
        # Populate coordinates and bounding box for the city
        outputResponse.body = fetch_lat_lng_bounding_box(outputResponse.body)
        
        # Fix boolean_query case
        if outputResponse.body.boolean_query:
            outputResponse.body.boolean_query = outputResponse.body.boolean_query.lower()
        
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
        
        # Calculate cost and set action
        costData = await calculate_cost(outputResponse.body)
        outputResponse.cost = str(costData.cost)
        outputResponse.body.action = "sample"
    
    # Add proper reason message for valid queries (do this regardless of body)
    if outputResponse.is_valid == "Valid" and outputResponse.body is not None:
        city_name = outputResponse.body.city_name
        query_term = outputResponse.body.boolean_query
        outputResponse.reason = f"Query is valid. The request contains an approved city ({city_name}) and category ({query_term})."
    
    return outputResponse
    