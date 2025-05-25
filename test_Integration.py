# test_run_Integration_test.py
#!/usr/bin/env python3
import pytest
import sys
import os
import subprocess
import logging
import time
import json
from contextlib import contextmanager

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
        self.test_port = test_port
        self.server_process = None

    @contextmanager
    def server_context(self):
        """Context manager for server lifecycle"""
        try:
            self.setup_test_environment()
            if not self.start_server():
                raise RuntimeError("Failed to start test server")
            
            yield {
                "port": self.test_port,
                "base_url": f"http://localhost:{self.test_port}",
                "api_base": f"http://localhost:{self.test_port}/fastapi",
            }
        finally:
            self.cleanup()

    def setup_test_environment(self):
        """Set up test environment - sets TEST_MODE and loads database config"""
        logger.info("🔧 Setting up test environment...")
        os.environ["TEST_MODE"] = "true"
        
        # Load database configuration from secrets
        try:
            with open("secrets_test/postgres_db.json", "r") as file:
                config = json.load(file)
                db_url = config["DATABASE_URL"]
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

    def start_server(self, timeout=120):
        """Start the FastAPI server in test mode with proper environment"""
        logger.info(f"🚀 Starting test server on port {self.test_port}...")
        
        cmd = [
            sys.executable,
            "-m", "uvicorn", "fastapi_app:app",
            "--reload",
            "--host", "localhost", 
            "--port", str(self.test_port),
        ]
        
        # Prepare environment variables for the server process
        env = os.environ.copy()
        env.update({
            "TEST_MODE": "true",
            "PORT": str(self.test_port),
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
                logger.info(f"✅ Test server started successfully on port {self.test_port}")
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
        check_interval = 10
        last_check_time = 0

        while time.time() - start_time < timeout:
            current_time = time.time()
            
            if self.server_process.poll() is not None:
                logger.error("💀 Server process terminated unexpectedly")
                return False
            
            if current_time - last_check_time >= check_interval:
                try:
                    from http.client import HTTPConnection
                    conn = HTTPConnection(f"localhost:{self.test_port}")
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
        logger.info("⏳ Waiting 5 seconds for background tasks and cache updates...")
        time.sleep(5)
        
        self.stop_server()
        os.environ.pop("TEST_MODE", None)
        os.environ.pop("DATABASE_URL", None)
        logger.info("✅ Test environment cleaned up")

def main():
    """Main entry point with enhanced pytest integration"""
    print("\n" + "="*80)
    print("🧪 INTEGRATION TEST RUNNER")
    print("="*80)
    logger.info("🚀 Starting Integration Test Runner...")
    logger.info("📋 This will start the server in TEST_MODE and run integration tests")
    
    # Start server and run pytest
    manager = TestServerManager(test_port=8080)
    
    with manager.server_context() as server_info:
        logger.info(f"🌐 Server running at: {server_info['base_url']}")
        
        # Run pytest with simple, working options (removed --dist=no)
        pytest_args = [
            "tests/integration/",
            "-v",                           # Verbose output
            "-s",                           # Don't capture output  
            "--tb=short",                   # Short traceback format
            "--maxfail=3",                  # Stop after 3 failures
            "--color=yes",                  # Force colored output
            "--show-capture=no",            # Don't show captured output
            "--durations=10",               # Show 10 slowest tests
        ]
        
        # Add coverage if available
        try:
            import pytest_cov
            pytest_args.extend([
                "--cov=backend_common", 
                "--cov-report=term-missing:skip-covered",
                "--cov-report=html:htmlcov"
            ])
            logger.info("📊 Coverage reporting enabled")
        except ImportError:
            logger.info("📊 Coverage not available (install pytest-cov for coverage)")
        
        print("\n" + "="*80)
        print("🔬 RUNNING TESTS")
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