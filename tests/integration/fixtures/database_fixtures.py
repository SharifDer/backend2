# tests/integration/fixtures/database_fixtures.py
import logging
import json
import os
import asyncpg
from datetime import datetime, timezone
from typing import List, Dict, Any, Set
from pathlib import Path
from .user_fixtures import UserData

logger = logging.getLogger(__name__)

class DatabaseSeeder:
    """Handles database seeding for integration tests"""
    
    def __init__(self, test_run_id: str):
        self.test_run_id = test_run_id
        self.created_tables: Set[str] = set()
        self.seeded_data: Dict[str, List[str]] = {}  # table_name -> list of primary keys
        self.db_seed_data_dir = Path(__file__).parent.parent / "db_seed_data"
        self._connection = None
    
    def _get_sync_connection(self):
        """Get a synchronous database connection"""
        if self._connection is None or self._connection.closed:  # ✅ Fixed: removed ()
            import os
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise Exception("DATABASE_URL environment variable not set")
            
            # Create synchronous connection
            import psycopg2
            self._connection = psycopg2.connect(database_url)
            self._connection.autocommit = True
            logger.info("🔌 Created synchronous database connection")
        
        return self._connection
    
    def _execute_sync(self, query: str, *params):
        """Execute database query synchronously using psycopg2"""
        conn = self._get_sync_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # For SELECT queries, return results
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return None
        except Exception as e:
            logger.error(f"❌ Database query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            cursor.close()
    
    def _load_db_seed_data(self, filename: str) -> Dict[str, Any]:
        """Load test seed data from JSON file"""
        file_path = self.db_seed_data_dir / filename
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"❌ Test seed data file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in test data file {file_path}: {e}")
            raise
    
    def _substitute_template_vars(self, data: Any, substitutions: Dict[str, str]) -> Any:
        """Recursively substitute template variables in data"""
        if isinstance(data, dict):
            return {k: self._substitute_template_vars(v, substitutions) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_template_vars(item, substitutions) for item in data]
        elif isinstance(data, str):
            result = data
            for var, value in substitutions.items():
                result = result.replace(f"{{{var}}}", str(value))
            return result
        else:
            return data
    
    def seed_db_ggl_maps_data(self, data_types: List[str] = None) -> Dict[str, Any]:
        """
        Seed Google Maps test data from JSON file
        
        Args:
            data_types: List of data types to seed (e.g., ['supermarket', 'coffee_shop_search'])
                       If None, seeds all available data types
        """
        table_name = "schema_marketplace.google_maps_test_raw"
        
        # Create the test table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS schema_marketplace.google_maps_test_raw (
                filename TEXT PRIMARY KEY,
                request_data TEXT,
                response_data TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._execute_sync(create_table_query)
        self.created_tables.add(table_name)
        logger.info(f"✅ Created/verified table: {table_name}")
        
        # Load test data from JSON
        google_maps_seed_data = self._load_db_seed_data("google_maps_raw.json")
        
        # If no specific data types requested, seed all
        if data_types is None:
            data_types = list(google_maps_seed_data.keys())
        
        substitutions = {"test_run_id": self.test_run_id}
        filenames = []
        variables = {}
        
        for data_type in data_types:
            if data_type not in google_maps_seed_data:
                logger.warning(f"⚠️ Data type '{data_type}' not found in google_maps_raw.json")
                continue
            
            test_seed_data = google_maps_seed_data[data_type]
            
            # Substitute template variables
            filename = self._substitute_template_vars(test_seed_data["filename_template"], substitutions)
            request_data = self._substitute_template_vars(test_seed_data["request_data"], substitutions)
            response_data = self._substitute_template_vars(test_seed_data["response_data"], substitutions)
            
            # Insert into database
            self._execute_sync(
                """
                INSERT INTO schema_marketplace.google_maps_test_raw 
                (filename, request_data, response_data, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (filename) DO UPDATE
                SET response_data = EXCLUDED.response_data
                """,
                filename,
                json.dumps(request_data),
                json.dumps(response_data),
                datetime.now(timezone.utc)
            )
            
            filenames.append(filename)
            
            # Extract place IDs for variables
            places = response_data.get("places", [])
            for i, place in enumerate(places):
                place_id = place.get("id", "")
                variables[f"{data_type}_place_id_{i}"] = place_id
                if i == 0:  # First place gets the generic name
                    variables[f"{data_type}_place_id"] = place_id
            
            variables[f"{data_type}_filename"] = filename
            
            logger.info(f"✅ Seeded Google Maps data type: {data_type}")
        
        # Track for cleanup
        if table_name not in self.seeded_data:
            self.seeded_data[table_name] = []
        self.seeded_data[table_name].extend(filenames)
        
        logger.info(f"✅ Seeded Google Maps test data for types: {data_types}")
        return variables
    
    def seed_transformed_datasets(self, user_data: UserData, dataset_types: List[str] = None) -> Dict[str, Any]:
        """
        Seed transformed dataset data from JSON file
        
        Args:
            user_data: User data for substitution
            dataset_types: List of dataset types to seed (e.g., ['supermarket_dataset', 'coffee_dataset'])
        """
        table_name = "schema_marketplace.datasets"
        
        # Create table if needed
        create_table_query = """
            CREATE TABLE IF NOT EXISTS schema_marketplace.datasets (
                filename TEXT PRIMARY KEY,
                request_data TEXT,
                response_data TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._execute_sync(create_table_query)
        self.created_tables.add(table_name)
        logger.info(f"✅ Created/verified table: {table_name}")
        
        # Load test data from JSON
        seed_dataset_data = self._load_db_seed_data("transformed_datasets.json")
        
        # If no specific dataset types requested, seed all
        if dataset_types is None:
            dataset_types = list(seed_dataset_data.keys())
        
        substitutions = {
            "test_run_id": self.test_run_id,
            "user_id": user_data.user_id
        }
        
        filenames = []
        variables = {}
        
        for dataset_type in dataset_types:
            if dataset_type not in seed_dataset_data:
                logger.warning(f"⚠️ Dataset type '{dataset_type}' not found in transformed_datasets.json")
                continue
            
            seed_test_data = seed_dataset_data[dataset_type]
            
            # Substitute template variables
            filename = self._substitute_template_vars(seed_test_data["filename_template"], substitutions)
            request_data = self._substitute_template_vars(seed_test_data["request_data"], substitutions)
            response_data = self._substitute_template_vars(seed_test_data["response_data"], substitutions)
            
            # Insert into database
            self._execute_sync(
                """
                INSERT INTO schema_marketplace.datasets 
                (filename, request_data, response_data, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (filename) DO UPDATE
                SET response_data = EXCLUDED.response_data
                """,
                filename,
                json.dumps(request_data),
                json.dumps(response_data),
                datetime.now(timezone.utc)
            )
            
            filenames.append(filename)
            variables[f"{dataset_type}_id"] = filename
            
            # Extract feature IDs for variables
            features = response_data.get("features", [])
            for i, feature in enumerate(features):
                feature_id = feature.get("properties", {}).get("id", "")
                variables[f"{dataset_type}_feature_id_{i}"] = feature_id
                if i == 0:  # First feature gets the generic name
                    variables[f"{dataset_type}_feature_id"] = feature_id
            
            logger.info(f"✅ Seeded transformed dataset: {dataset_type}")
        
        # Track for cleanup
        if table_name not in self.seeded_data:
            self.seeded_data[table_name] = []
        self.seeded_data[table_name].extend(filenames)
        
        logger.info(f"✅ Seeded transformed datasets for types: {dataset_types}")
        return variables
    
    def seed_real_estate_data(self, property_types: List[str] = None) -> Dict[str, Any]:
        """
        Seed real estate test data from JSON file
        
        Args:
            property_types: List of property types to seed (e.g., ['residential_properties', 'commercial_properties'])
        """
        table_name = "schema_marketplace.real_estate_test_data"
        
        # Create the test table
        create_table_query = """
            CREATE TABLE IF NOT EXISTS schema_marketplace.real_estate_test_data (
                filename TEXT PRIMARY KEY,
                request_data TEXT,
                response_data TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._execute_sync(create_table_query)
        self.created_tables.add(table_name)
        logger.info(f"✅ Created/verified table: {table_name}")
        
        # Load test data from JSON
        real_estate_data = self._load_db_seed_data("real_estate_data.json")
        
        # If no specific property types requested, seed all
        if property_types is None:
            property_types = list(real_estate_data.keys())
        
        substitutions = {"test_run_id": self.test_run_id}
        filenames = []
        variables = {}
        
        for property_type in property_types:
            if property_type not in real_estate_data:
                logger.warning(f"⚠️ Property type '{property_type}' not found in real_estate_data.json")
                continue
            
            test_data = real_estate_data[property_type]
            
            # Substitute template variables
            filename = self._substitute_template_vars(test_data["filename_template"], substitutions)
            request_data = self._substitute_template_vars(test_data["request_data"], substitutions)
            response_data = self._substitute_template_vars(test_data["response_data"], substitutions)
            
            # Insert into database
            self._execute_sync(
                """
                INSERT INTO schema_marketplace.real_estate_test_data 
                (filename, request_data, response_data, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (filename) DO UPDATE
                SET response_data = EXCLUDED.response_data
                """,
                filename,
                json.dumps(request_data),
                json.dumps(response_data),
                datetime.now(timezone.utc)
            )
            
            filenames.append(filename)
            variables[f"{property_type}_filename"] = filename
            
            # Extract property IDs for variables
            properties = response_data.get("properties", [])
            for i, prop in enumerate(properties):
                prop_id = prop.get("id", "")
                variables[f"{property_type}_property_id_{i}"] = prop_id
                if i == 0:  # First property gets the generic name
                    variables[f"{property_type}_property_id"] = prop_id
            
            logger.info(f"✅ Seeded real estate data type: {property_type}")
        
        # Track for cleanup
        if table_name not in self.seeded_data:
            self.seeded_data[table_name] = []
        self.seeded_data[table_name].extend(filenames)
        
        logger.info(f"✅ Seeded real estate test data for types: {property_types}")
        return variables
    
    def close_connection(self):
        """Close the database connection"""
        if self._connection and not self._connection.closed:  # ✅ Fixed: removed ()
            self._connection.close()
            logger.info("🔌 Closed database connection")

class DatabaseCleanupManager:
    """Handles synchronous cleanup of database test data"""
    
    def __init__(self):
        self.cleanup_registry: Set[str] = set()
        self._connection = None
    
    def _get_sync_connection(self):
        """Get a synchronous database connection"""
        if self._connection is None or self._connection.closed:  # ✅ Fixed: removed ()
            import os
            database_url = os.environ.get("DATABASE_URL")
            if not database_url:
                raise Exception("DATABASE_URL environment variable not set")
            
            # Create synchronous connection
            import psycopg2
            self._connection = psycopg2.connect(database_url)
            self._connection.autocommit = True
        
        return self._connection
    
    def register_table_for_cleanup(self, table_name: str):
        """Register a table for cleanup"""
        self.cleanup_registry.add(table_name)
    
    def _execute_sync(self, query: str, *params):
        """Execute database query synchronously using psycopg2"""
        conn = self._get_sync_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return None
        except Exception as e:
            logger.error(f"❌ Database cleanup query failed: {e}")
            raise
        finally:
            cursor.close()
    
    def cleanup_all_registered(self):
        """Synchronously clean up all registered tables"""
        if not self.cleanup_registry:
            logger.info("No database tables registered for cleanup")
            return
        
        cleanup_count = 0
        for table_name in list(self.cleanup_registry):
            try:
                self._execute_sync(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(f"🗑️ Dropped table: {table_name}")
                cleanup_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up table {table_name}: {e}")
        
        self.cleanup_registry.clear()
        logger.info(f"🧹 Cleaned up {cleanup_count} database tables")
        
        # Close connection after cleanup
        if self._connection and not self._connection.closed:  # ✅ Fixed: removed ()
            self._connection.close()
    
    def cleanup_specific_data(self, database_seeder: DatabaseSeeder):
        """Synchronously clean up specific seeded data"""
        for table_name, primary_keys in database_seeder.seeded_data.items():
            try:
                for pk in primary_keys:
                    self._execute_sync(f"DELETE FROM {table_name} WHERE filename = %s", pk)
                logger.info(f"🧹 Cleaned up {len(primary_keys)} records from {table_name}")
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up data from {table_name}: {e}")
        
        # Close seeder connection after cleanup
        database_seeder.close_connection()