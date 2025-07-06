#!/usr/bin/env python3
"""
Port Killer Module - Aggressive port cleanup for Windows and Unix systems
"""
import subprocess
import logging
import time
import platform
import socket

logger = logging.getLogger(__name__)


class PortKiller:
    """Handles aggressive port cleanup across different operating systems"""
    
    def __init__(self):
        self.os_name = platform.system()
    
    def kill_processes_on_port(self, port):
        """Forcibly kill any processes running on the specified port"""
        logger.info(f"🔪 Forcibly killing any processes on port {port}...")
        
        try:
            if self.os_name == "Windows":
                self._kill_windows_processes(port)
            else:
                self._kill_unix_processes(port)
                
        except Exception as e:
            logger.error(f"💥 Unexpected error killing processes on port {port}: {e}")
        
        # Give the OS a moment to fully clean up after kill attempts
        self._wait_for_cleanup()
        
        # Verification step - check if any processes are still running on the port
        logger.info(f"🔍 Verifying that port {port} is actually free...")
        remaining_processes = self._get_remaining_processes(port)
        
        if remaining_processes:
            logger.error(f"❌ CRITICAL: {len(remaining_processes)} processes still running on port {port}!")
            for proc_info in remaining_processes:
                logger.error(f"❌ Still running: {proc_info}")
            logger.error("❌ Cannot proceed with tests - aborting to prevent conflicts")
            logger.error("💡 Try manually killing these processes or using a different port")
            raise RuntimeError(f"Failed to free port {port} - {len(remaining_processes)} processes still running")
            
        logger.info(f"✅ Port {port} verification passed - port is completely free")
        logger.info(f"🏁 Finished cleaning up port {port}")

    def _kill_windows_processes(self, port):
        """Kill processes on Windows using multiple methods"""
        try:
            # Find processes using the port
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            pids_to_kill = []
            for line in result.stdout.split('\n'):
                if f":{port}" in line and ("LISTENING" in line or "ESTABLISHED" in line):
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids_to_kill.append(pid)
            
            # Remove duplicates
            pids_to_kill = list(set(pids_to_kill))
            
            if pids_to_kill:
                logger.info(f"🎯 Found {len(pids_to_kill)} processes to kill: {pids_to_kill}")
                
                for pid in pids_to_kill:
                    self._kill_windows_process(pid)
            else:
                logger.info(f"✅ No processes found on port {port}")
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout running netstat command")
        except Exception as e:
            logger.warning(f"⚠️ Error finding processes on Windows: {e}")

    def _kill_windows_process(self, pid):
        """Try multiple methods to kill a Windows process"""
        try:
            logger.info(f"🔪 Attempting to kill PID: {pid}")
            
            # Method 1: Standard force kill
            result1 = subprocess.run(
                ["taskkill", "/F", "/PID", pid], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result1.returncode == 0:
                logger.info(f"💀 Method 1 - Killed process PID: {pid}")
                return
            
            # Method 2: Try with /T (kill tree)
            logger.warning(f"⚠️ Method 1 failed for PID {pid}, trying method 2...")
            result2 = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", pid], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            if result2.returncode == 0:
                logger.info(f"💀 Method 2 - Killed process PID: {pid}")
                return
            
            logger.error(f"❌ All methods failed to kill PID {pid}")
            
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Timeout killing PID: {pid}")
        except Exception as e:
            logger.warning(f"⚠️ Exception killing PID {pid}: {e}")

    def _kill_unix_processes(self, port):
        """Kill processes on Unix/Linux systems"""
        try:
            # Find processes using the port
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                logger.info(f"🎯 Found {len(pids)} processes to kill: {pids}")
                
                for pid in pids:
                    if pid.strip():
                        self._kill_unix_process(pid.strip())
            else:
                logger.info(f"✅ No processes found on port {port}")
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Timeout running lsof command")
        except FileNotFoundError:
            logger.warning("⚠️ lsof command not available")
        except Exception as e:
            logger.warning(f"⚠️ Error finding processes on Unix: {e}")

    def _kill_unix_process(self, pid):
        """Kill a Unix process using SIGTERM then SIGKILL"""
        try:
            # Try SIGTERM first
            subprocess.run(["kill", pid], timeout=2)
            time.sleep(0.5)
            
            # Check if still running, then SIGKILL
            check_result = subprocess.run(
                ["kill", "-0", pid], 
                capture_output=True, 
                timeout=2
            )
            if check_result.returncode == 0:
                subprocess.run(["kill", "-9", pid], timeout=2)
            
            logger.info(f"💀 Killed process PID: {pid}")
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Timeout killing PID: {pid}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to kill PID {pid}: {e}")

    def _wait_for_cleanup(self):
        """Wait for the OS to clean up processes"""
        if self.os_name == "Windows":
            logger.info("⏳ Waiting 2 seconds for Windows to clean up processes...")
            time.sleep(2)
        else:
            logger.info("⏳ Waiting 1 second for Unix cleanup...")
            time.sleep(1)

    def _get_remaining_processes(self, port):
        """Get list of processes still using the port after cleanup attempts"""
        remaining_processes = []
        
        try:
            if self.os_name == "Windows":
                remaining_processes = self._get_remaining_windows_processes(port)
            else:
                remaining_processes = self._get_remaining_unix_processes(port)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️ Timeout during port verification for port {port}")
            remaining_processes.append("Unknown process (verification timeout)")
        except Exception as e:
            logger.warning(f"⚠️ Error checking for remaining processes: {e}")
        
        # If we couldn't detect processes with system commands, try socket binding
        if not remaining_processes:
            remaining_processes = self._check_port_with_socket(port)
        
        return remaining_processes

    def _get_remaining_windows_processes(self, port):
        """Check for remaining processes on Windows"""
        remaining_processes = []
        
        # Check with netstat
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        
        for line in result.stdout.split('\n'):
            if f":{port}" in line and ("LISTENING" in line or "ESTABLISHED" in line):
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit():
                        remaining_processes.append(f"PID {pid}: {line.strip()}")
        
        return remaining_processes

    def _get_remaining_unix_processes(self, port):
        """Check for remaining processes on Unix/Linux"""
        remaining_processes = []
        
        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"], 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        remaining_processes.append(f"PID {pid.strip()}")
                        
        except FileNotFoundError:
            pass  # lsof not available
        
        return remaining_processes

    def _check_port_with_socket(self, port):
        """Final check using socket binding"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.settimeout(5)
            test_socket.bind(('localhost', port))
            test_socket.close()
            # Socket binding succeeded, port is free
            return []
        except socket.error as e:
            # Socket binding failed, something is using the port
            return [f"Unknown process (socket error: {e})"]


def find_available_port(start_port=8080, max_attempts=30):
    """
    Find an available port starting from start_port.
    
    Args:
        start_port (int): Port to start searching from
        max_attempts (int): Maximum number of ports to check
        
    Returns:
        int: Available port number
        
    Raises:
        RuntimeError: If no available port is found
    """
    for attempt in range(max_attempts):
        test_port = start_port + attempt
        
        try:
            # Test TCP port
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.settimeout(2)
            test_socket.bind(('localhost', test_port))
            test_socket.close()
            return test_port
        except socket.error:
            continue
    
    raise RuntimeError(f"Could not find available port after {max_attempts} attempts starting from {start_port}")


def is_port_available(port):
    """
    Check if a specific port is available.
    
    Args:
        port (int): Port number to check
        
    Returns:
        bool: True if port is available, False otherwise
    """
    try:
        # Test TCP port
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.settimeout(2)
        test_socket.bind(('localhost', port))
        test_socket.close()
        return True
    except socket.error:
        return False


# Convenience function for backward compatibility
def kill_processes_on_port(port):
    """Convenience function to kill processes on a port"""
    killer = PortKiller()
    killer.kill_processes_on_port(port)
