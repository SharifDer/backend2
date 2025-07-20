# FastAPI Application Organization

This document describes how the FastAPI application has been organized into modular routers while maintaining all existing URLs.

## Router Structure

The application has been organized into 5 main router modules:

### 1. Authentication (`routers/authentication.py`)
**Tag:** Authentication
**Endpoints:**
- `/fastapi/login` - User login
- `/fastapi/refresh_token` - Token refresh
- `/fastapi/reset_password` - Password reset
- `/fastapi/confirm_reset` - Confirm password reset
- `/fastapi/change_password` - Change password
- `/fastapi/change_email` - Change email
- `/fastapi/user_profile` - Get user profile
- `/fastapi/create_user_profile` - Create user profile
- `/fastapi/update_user_profile` - Update user profile

### 2. Data & Layers Management (`routers/data_layers.py`)
**Tag:** Data & Layers
**Endpoints:**
- Basic data endpoints (acknowledgment, catalog collection, layer collection, country/city data)
- Dataset fetching (`/fastapi/fetch_dataset`, `/fastapi/process_llm_query`)
- Layer management (`/fastapi/save_layer`, `/fastapi/delete_layer`, `/fastapi/user_layers`)
- Cost calculation (`/fastapi/cost_calculator`)
- Data visualization (gradient colors, recoloring, filtering)
- Street view checking

### 3. Catalogs Management (`routers/catalogs.py`)
**Tag:** Catalogs
**Endpoints:**
- `/fastapi/save_producer_catalog` - Save producer catalog
- `/fastapi/delete_producer_catalog` - Delete producer catalog
- `/fastapi/user_catalogs` - Get user catalogs
- `/fastapi/fetch_ctlg_lyrs` - Fetch catalog layers
- `/fastapi/save_draft_catalog` - Save draft catalog

### 4. Stripe Payments (`routers/stripe_payments.py`)
**Tag:** Stripe
**Endpoints:**
- **Customers:** create, update, list, fetch, get spending
- **Wallet:** top up, fetch, deduct
- **Subscriptions:** create, update, deactivate
- **Payment Methods:** update, attach, detach, list, set default
- **Products:** create, update, delete, list

### 5. Analysis & Intelligence (`routers/analysis_intelligence.py`)
**Tag:** Analysis & Intelligence
**Endpoints:**
- `/fastapi/distance_drive_time_polygon` - Distance/drive time analysis
- `/fastapi/fetch_population_by_viewport` - Population data by viewport
- `/fastapi/temp_sales_man_problem` - Sales territory optimization
- `/fastapi/hub_expansion_analysis` - Hub expansion analysis

## Implementation Details

### Main Application File (`fastapi_app.py`)
- Cleaned up to contain only core application setup
- All original endpoints are commented out in a multi-line string
- Router includes are added after app creation:
  ```python
  app.include_router(auth_router, tags=["Authentication"])
  app.include_router(data_layers_router, tags=["Data & Layers"])
  app.include_router(catalogs_router, tags=["Catalogs"])
  app.include_router(stripe_router, tags=["Stripe"])
  app.include_router(analysis_router, tags=["Analysis & Intelligence"])
  ```

### Router Organization (`routers/__init__.py`)
- All routers are properly exported
- Easy to import in main application

## Benefits of This Organization

1. **Maintainability:** Each router focuses on a specific domain
2. **Scalability:** Easy to add new endpoints to appropriate modules
3. **Team Development:** Different team members can work on different modules
4. **Code Clarity:** Related endpoints are grouped together
5. **URL Preservation:** All existing URLs remain exactly the same
6. **Testing:** Each module can be tested independently

## Usage

All existing URLs continue to work exactly as before. The modular organization is transparent to API consumers.

The FastAPI automatic documentation (Swagger) will now show endpoints organized by tags, making it easier to navigate.

## Future Enhancements

- Add route-specific middleware to individual routers
- Implement router-specific dependency injection
- Add module-specific error handling
- Consider further sub-module organization as the application grows
