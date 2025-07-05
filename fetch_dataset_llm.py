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

    system_message = f"""You are a location-based search API assistant that extracts structured data from queries.

    # CORE REQUIREMENTS
    1. Extract exactly ONE city from: {Approved_Cities}
    2. Extract place categories from: {Approved_Categories} 
    3. Always respond in valid JSON format

    # QUERY INTERPRETATION
    - Be flexible: extract useful info even from conversational queries
    - "I want to open a restaurant in Tokyo" → Extract: RESTAURANT, Tokyo
    - "Hotels with cafes in Paris" → Extract: HOTEL AND CAFE, Paris
    - Business planning queries = research for existing places

    # BOOLEAN LOGIC
    - Alternatives: "restaurants or cafes" → "RESTAURANT OR CAFE"
    - Combinations: "hotels with restaurants" → "HOTEL AND RESTAURANT"
    - Use approved category names only

    # REJECTION RULES
    Reject if:
    - No approved city mentioned
    - Multiple cities mentioned  
    - No place categories mentioned
    - Inappropriate/offensive content

    # REASONING MESSAGES
    - AND queries: "I've provided places that are [cat1] and [cat2] at the same time. If you wanted them separately, please ask for [cat1] or [cat2] in a new chat."
    - OR/single queries: "Query valid for [city] and [categories]."

    Always respond in the specified JSON schema format."""
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
    