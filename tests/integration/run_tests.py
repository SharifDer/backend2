# test_run_Integration_test.py
#!/usr/bin/env python3
import pytest
import sys
import os
import subprocess
import logging
import time
import json
import psycopg2
import argparse
import socket
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from urllib.parse import urlparse
from contextlib import contextmanager
from port_killer import PortKiller

# Set up logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

class TestServerManager:
    """Manages test server with proper database configuration"""
    
    def __init__(self, test_port=8080):
        self.preferred_port = test_port
        self.actual_port = None
        self.server_process = None
        self.port_killer = PortKiller()

    def find_available_port(self, start_port=None, max_attempts=50):
        """Find an available port starting from the specified port"""
        if start_port is None:
            start_port = self.preferred_port  # Start searching from preferred port itself
            
        logger.info(f"🔍 Looking for available port starting from {start_port}...")
        
        for attempt in range(max_attempts):
            test_port = start_port + attempt
                
            if self._is_port_available(test_port):
                logger.info(f"✅ Found available port: {test_port}")
                # Double-check the port is really available by trying to bind again
                if self._verify_port_really_available(test_port):
                    return test_port
                else:
                    logger.info(f"⚠️ Port {test_port} failed verification, continuing search...")
                    continue
            else:
                logger.info(f"❌ Port {test_port} is occupied, trying next...")
        
        raise RuntimeError(f"❌ Could not find available port after {max_attempts} attempts starting from {start_port}")

    def _is_port_available(self, port):
        """Check if a port is available using multiple methods"""
        # Method 1: Try to bind to IPv4 localhost
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.settimeout(1)
            test_socket.bind(('127.0.0.1', port))
            test_socket.close()
        except socket.error:
            logger.info(f"Port {port} is not available on IPv4 (127.0.0.1)")
            return False
        
        # Method 2: Try to bind to all interfaces
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.settimeout(1)
            test_socket.bind(('0.0.0.0', port))
            test_socket.close()
        except socket.error:
            logger.info(f"Port {port} is not available on IPv4 (0.0.0.0)")
            return False
        
        # Method 3: Try to connect to the port (check if something is listening)
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex(('127.0.0.1', port))
            test_socket.close()
            if result == 0:
                logger.info(f"Port {port} has a service listening")
                return False
        except socket.error:
            pass  # Connection failed, which is good - means nothing is listening
        
        return True

    def kill_processes_on_port(self, port):
        """Forcibly kill any processes running on the specified port"""
        logger.info(f"🔪 Attempting to kill processes on port {port}...")
        try:
            self.port_killer.kill_processes_on_port(port)
            return True
        except Exception as e:
            logger.warning(f"⚠️ Failed to kill processes on port {port}: {e}")
            return False

    @contextmanager
    def server_context(self):
        """Context manager for server lifecycle"""
        try:
            # Step 1: Try to use preferred port
            self.actual_port = self._select_optimal_port()
            
            # Step 2: Setup environment and start server
            self.setup_test_environment()
            if not self.start_server():
                raise RuntimeError("Failed to start test server")
            
            yield {
                "port": self.actual_port,
                "base_url": f"http://localhost:{self.actual_port}",
                "api_base": f"http://localhost:{self.actual_port}/fastapi",
                "preferred_port": self.preferred_port,
                "port_changed": self.actual_port != self.preferred_port
            }
        finally:
            self.cleanup()

    def _select_optimal_port(self):
        """Select the optimal port with a focus on dynamic switching (skip unreliable port killing)"""
        logger.info(f"🎯 Attempting to use preferred port {self.preferred_port}...")
        
        # Skip the individual port check - go straight to comprehensive search
        # This ensures we get 8080 → 8081 → 8082 → 8083... sequence
        logger.info(f"🔄 Starting comprehensive port search from {self.preferred_port}...")
        logger.info("💡 Skipping port killing (unreliable on Windows) - using dynamic port selection")
        
        # Find available port starting from preferred port (8080, 8081, 8082...)
        available_port = self.find_available_port(self.preferred_port)
        
        if available_port == self.preferred_port:
            logger.info(f"✅ Using preferred port {available_port}")
        else:
            logger.info(f"🎯 Using alternative port: {available_port}")
            
        return available_port

    def setup_test_environment(self):
        """Set up test environment - sets TEST_MODE and loads database config"""
        logger.info("🔧 Setting up test environment...")
        os.environ["TEST_MODE"] = "true"
        
        # Load database configuration from secrets
        try:
            with open("secrets_test/postgres_db.json", "r") as file:
                config = json.load(file)
                db_url = config["DATABASE_URL"]
                logger.info("📊 Database configuration loaded from secrets_test/postgres_db.json")
                
                # Check if database exists and create it if needed
                self.check_and_create_database(db_url)
                
                # Set environment variable after successful database check/creation
                os.environ["DATABASE_URL"] = db_url
                
                logger.info("📊 Database configuration loaded from secrets_test/postgres_db.json")
        except FileNotFoundError:
            logger.error("❌ secrets_test/postgres_db.json not found!")
            raise
        except KeyError:
            logger.error("❌ DATABASE_URL not found in postgres_db.json!")
            raise
        except json.JSONDecodeError:
            logger.error("❌ Invalid JSON in postgres_db.json!")
            raise

        logger.info("✅ Test environment set up successfully")

    def check_and_create_database(self, db_url: str):
        """Check if database exists and create it if it doesn't"""
        logger.info("🔍 Checking database existence...")
        
        # Parse the database URL
        parsed = urlparse(db_url)
        db_name = parsed.path.lstrip('/')
        
        # Create connection URL without database name for initial connection
        admin_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
        
        try:
            # Try to connect to the target database first
            logger.info(f"🔗 Attempting to connect to database: {db_name}")
            test_conn = psycopg2.connect(db_url)
            test_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Database exists, always recreate schema and table for clean state
            logger.info(f"✅ Database '{db_name}' exists and is accessible")
            logger.info("� Recreating schema and table for clean test state...")
            
            # Always recreate schema and table
            self._create_schema_and_table(test_conn)
            test_conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                logger.info(f"📝 Database '{db_name}' does not exist, creating it...")
                return self._create_database(admin_url, db_name)
            else:
                logger.error(f"❌ Database connection error: {e}")
                raise
        except Exception as e:
            logger.error(f"💥 Unexpected error checking database: {e}")
            raise
    
    def _create_database(self, admin_url: str, db_name: str):
        """Create the database if it doesn't exist"""
        try:
            # Connect to postgres database to create new database
            logger.info(f"🔗 Connecting to PostgreSQL server to create database '{db_name}'...")
            admin_conn = psycopg2.connect(admin_url)
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = admin_conn.cursor()
            
            # Check if database already exists (race condition protection)
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if cursor.fetchone():
                logger.info(f"✅ Database '{db_name}' already exists (created by another process)")
                cursor.close()
                admin_conn.close()
                return True
            
            # Create the database
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info(f"✅ Successfully created database: {db_name}")
            
            cursor.close()
            admin_conn.close()
            
            # Verify the database was created by connecting to it and create schema/table
            db_conn = psycopg2.connect(admin_url.replace("/postgres", f"/{db_name}"))
            db_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info(f"✅ Verified database '{db_name}' is accessible")
            
            # Create schema and table
            self._create_schema_and_table(db_conn)
            
            db_conn.close()
            
            return True
            
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to create database '{db_name}': {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected error creating database: {e}")
            raise

    def _create_schema_and_table(self, db_conn):
        """Drop and recreate the schema_marketplace schema and datasets table"""
        try:
            cursor = db_conn.cursor()
            
            # Drop table if it exists (this will also drop any indexes)
            logger.info("🗑️ Dropping table 'datasets' if it exists...")
            cursor.execute("DROP TABLE IF EXISTS schema_marketplace.datasets CASCADE")
            logger.info("✅ Table dropped successfully")
            
            # Create schema if it doesn't exist
            logger.info("📋 Creating schema 'schema_marketplace'...")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS schema_marketplace")
            logger.info("✅ Schema 'schema_marketplace' created successfully")
            
            # Create table (clean slate)
            logger.info("📋 Creating table 'datasets' in schema_marketplace...")
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS schema_marketplace.datasets
                (
                    filename text COLLATE pg_catalog."default" NOT NULL,
                    request_data jsonb,
                    response_data jsonb,
                    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT datasets_pkey PRIMARY KEY (filename)
                )
            """
            cursor.execute(create_table_sql)
            logger.info("✅ Table 'schema_marketplace.datasets' created successfully")
            
            cursor.close()
            
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to create schema and table: {e}")
            raise
        except Exception as e:
            logger.error(f"💥 Unexpected error creating schema and table: {e}")
            raise

    def start_server(self, timeout=120):
        """Start the FastAPI server in test mode with proper environment"""
        logger.info(f"🚀 Starting test server on port {self.actual_port}...")
        
        cmd = [
            sys.executable,
            "-m", "uvicorn", "fastapi_app:app",
            "--host", "127.0.0.1",  # Bind specifically to IPv4 localhost
            "--port", str(self.actual_port),
        ]
        
        # Prepare environment variables for the server process
        env = os.environ.copy()
        env.update({
            "TEST_MODE": "true",
            "PORT": str(self.actual_port),
            "TEST_SERVER_PORT": str(self.actual_port),  # For pytest fixtures
            "DATABASE_URL": os.environ["DATABASE_URL"]
        })
        
        try:
            logger.info(f"📋 Launching server: {' '.join(cmd)}")
            
            self.server_process = subprocess.Popen(
                cmd,
                env=env,
                cwd=os.getcwd(),
            )
            
            logger.info("⏳ Server process started, waiting for it to be ready...")
            
            if self._wait_for_server(timeout):
                logger.info(f"✅ Test server started successfully on port {self.actual_port}")
                return True
            else:
                logger.error("❌ Server failed to start within timeout")
                self.stop_server()
                return False
                
        except Exception as e:
            logger.error(f"💥 Failed to start server: {e}")
            return False

    def _wait_for_server(self, timeout):
        """Wait for server to be ready to accept connections"""
        start_time = time.time()
        check_interval = 20
        last_check_time = 0

        while time.time() - start_time < timeout:
            current_time = time.time()
            
            if self.server_process.poll() is not None:
                logger.error("💀 Server process terminated unexpectedly")
                return False
            
            if current_time - last_check_time >= check_interval:
                try:
                    from http.client import HTTPConnection
                    conn = HTTPConnection(f"localhost:{self.actual_port}")
                    conn.request("GET", "/fastapi/fetch_acknowlg_id")
                    response = conn.getresponse()
                    conn.close()

                    if response.status in [200, 404]:
                        return True

                except (ConnectionRefusedError, OSError):
                    elapsed = current_time - start_time
                    logger.info(f"⏳ Server not ready yet (after {elapsed:.1f}s)...")
                
                last_check_time = current_time

            time.sleep(2)

        return False

    def stop_server(self):
        """Stop the test server"""
        if self.server_process:
            logger.info("🛑 Stopping test server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Graceful shutdown failed, force killing server")
                self.server_process.kill()
                self.server_process.wait()

            self.server_process = None
            logger.info("✅ Test server stopped")

    def cleanup(self):
        """Clean up test environment with proper delays"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Give background tasks time to complete
        logger.info("⏳ Waiting 3 seconds for background tasks and cache updates...")
        time.sleep(3)
        
        self.stop_server()
        
        # Don't rely on port killing - let the OS handle cleanup naturally
        # The dynamic port system will handle conflicts on next run
        
        os.environ.pop("TEST_MODE", None)
        os.environ.pop("DATABASE_URL", None)
        os.environ.pop("TEST_SERVER_PORT", None)
        logger.info("✅ Test environment cleaned up")

    def _verify_port_really_available(self, port):
        """Double verification that a port is really available"""
        try:
            # Create a test server socket and immediately close it
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.settimeout(1)
            test_socket.bind(('127.0.0.1', port))
            test_socket.listen(1)
            test_socket.close()
            
            # Also check if we can bind to all interfaces
            test_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket2.settimeout(1)
            test_socket2.bind(('0.0.0.0', port))
            test_socket2.close()
            
            return True
        except socket.error as e:
            logger.info(f"Port {port} verification failed: {e}")
            return False

def parse_arguments():
    """Parse command line arguments for test runner"""
    parser = argparse.ArgumentParser(
        description="Integration Test Runner - Run tests with server management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                                    # Run all tests
  python run_tests.py -t test_fetch_dataset_llm.py      # Run specific test file
  python run_tests.py -k test_valid_query               # Run tests matching pattern
  python run_tests.py -t test_fetch_dataset_llm.py -k valid_query  # Combine filters
  python run_tests.py --no-coverage                     # Run without coverage
        """
    )
    
    parser.add_argument(
        "-t", "--test", 
        help="Specific test file to run (e.g., test_fetch_dataset_llm.py)"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        help="Run tests matching this keyword/expression (pytest -k option)"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for test server (default: 8080)"
    )
    
    return parser.parse_args()

def main():
    """Main entry point with enhanced pytest integration"""
    args = parse_arguments()
    
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST RUNNER")
    print("="*80)
    logger.info("🚀 Starting Integration Test Runner...")
    logger.info("📋 This will start the server in TEST_MODE and run integration tests")
    logger.info(f"🚪 Using port: {args.port}")
    
    if args.test:
        logger.info(f"🎯 Running specific test: {args.test}")
    if args.keyword:
        logger.info(f"🔍 Filtering tests with keyword: {args.keyword}")
    
    # Start server and run pytest
    manager = TestServerManager(test_port=args.port)
    
    with manager.server_context() as server_info:
        if server_info["port_changed"]:
            print(f"⚠️ PORT CHANGED: Using port {server_info['port']} instead of preferred {server_info['preferred_port']}")
            logger.warning(f"⚠️ Port killer was unable to free port {server_info['preferred_port']}, using alternative port {server_info['port']}")
        else:
            print(f"✅ Using preferred port {server_info['port']}")
            logger.info(f"✅ Successfully using preferred port {server_info['port']}")
        
        logger.info(f"🌐 Server running at: {server_info['base_url']}")
        
        # Set environment variable for pytest fixtures
        os.environ["TEST_SERVER_PORT"] = str(server_info["port"])
        
        # Build pytest arguments based on user input
        if args.test:
            # If specific test file provided, run just that file
            test_path = args.test
            if not test_path.startswith("tests/integration/"):
                test_path = f"tests/integration/{test_path}"
            pytest_args = [test_path]
        else:
            # Run all integration tests
            pytest_args = ["tests/integration/"]
        
        # Add common pytest options
        pytest_args.extend([
            "-v",                           # Verbose output
            "-s",                           # Don't capture output  
            "--tb=short",                   # Short traceback format
            "--color=yes",                  # Force colored output
            "--show-capture=no",            # Don't show captured output
            "--durations=10",               # Show 10 slowest tests
            "-r", "A",                      # Show all test outcomes (passed, failed, skipped, etc.)
        ])
        
        # Add keyword filter if provided
        if args.keyword:
            pytest_args.extend(["-k", args.keyword])
        
        # Add coverage if available and not disabled
        if not args.no_coverage:
            try:
                import importlib.util
                if importlib.util.find_spec("pytest_cov"):
                    pytest_args.extend([
                        "--cov=backend_common", 
                        "--cov-report=term-missing:skip-covered",
                        "--cov-report=html:htmlcov"
                    ])
                    logger.info("📊 Coverage reporting enabled")
                else:
                    logger.info("📊 Coverage not available (install pytest-cov for coverage)")
            except ImportError:
                logger.info("📊 Coverage not available (install pytest-cov for coverage)")
        else:
            logger.info("📊 Coverage reporting disabled")
        
        print("\n" + "="*80)
        print("🔬 RUNNING TESTS")
        if args.test:
            print(f"🎯 Target: {args.test}")
        if args.keyword:
            print(f"🔍 Filter: {args.keyword}")
        print("="*80)
        
        # Run the tests
        exit_code = pytest.main(pytest_args)
    
    print("\n" + "="*80)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED!")
        logger.info("🎉 All tests passed!")
    else:
        print("❌ SOME TESTS FAILED!")
        logger.error("💥 Some tests failed!")
    print("="*80)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()