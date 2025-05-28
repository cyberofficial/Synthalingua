"""
Rate Limiter Module for Synthalingua

This module provides functionality to handle rate limiting in HTTP requests,
particularly for handling 429 Too Many Requests responses.

It implements adaptive delay strategies to automatically back off when rate
limits are encountered.
"""

import time
from typing import Dict, Optional
import threading

class RateLimiter:
    """
    A class to manage rate limiting for HTTP requests with adaptive delay.
    
    This class keeps track of delays for different endpoints/hosts and
    adjusts them when rate limiting errors are encountered.
    """
    
    def __init__(
        self, 
        initial_delay: float = 5.0, 
        backoff_step: float = 0.5,
        max_delay: float = 30.0
    ):
        """
        Initialize the RateLimiter.
        
        Args:
            initial_delay (float): Initial delay between requests in seconds.
            backoff_step (float): How much to increase delay when hitting rate limits.
            max_delay (float): Maximum delay between requests.
        """
        self.initial_delay = initial_delay
        self.backoff_step = backoff_step
        self.max_delay = max_delay
        self.delays: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def get_delay(self, host: str) -> float:
        """
        Get the current delay for a specific host.
        
        Args:
            host (str): The host/endpoint identifier.
            
        Returns:
            float: The current delay in seconds for this host.
        """
        with self._lock:
            return self.delays.get(host, self.initial_delay)
    
    def increase_delay(self, host: str) -> float:
        """
        Increase the delay for a host when rate limiting is encountered.
        
        Args:
            host (str): The host/endpoint identifier.
            
        Returns:
            float: The new delay time.
        """
        with self._lock:
            current = self.delays.get(host, self.initial_delay)
            new_delay = min(current + self.backoff_step, self.max_delay)
            self.delays[host] = new_delay
            return new_delay
    
    def reset_delay(self, host: str) -> None:
        """
        Reset the delay for a host back to the initial value.
        
        Args:
            host (str): The host/endpoint identifier.
        """
        with self._lock:
            self.delays[host] = self.initial_delay
    
    def wait_and_backoff(self, host: str, is_429: bool = False) -> float:
        """
        Wait for the required delay and increase it if rate limiting was encountered.
        
        Args:
            host (str): The host/endpoint identifier.
            is_429 (bool): Whether a 429 error was encountered.
            
        Returns:
            float: The delay that was used (after potential increase).
        """
        delay = self.get_delay(host)
        
        if is_429:
            delay = self.increase_delay(host)
        
        time.sleep(delay)
        return delay
    
    def handle_request(self, host: str, success: bool, was_rate_limited: bool = False) -> float:
        """
        Handle rate limiting logic for a request.
        
        This method manages the delay for a host based on whether the request was successful
        and whether it encountered rate limiting (429) errors.
        
        Args:
            host (str): The host/endpoint identifier.
            success (bool): Whether the request was successful.
            was_rate_limited (bool): Whether the request encountered rate limiting.
            
        Returns:
            float: The current delay for this host.
        """
        with self._lock:
            if success:
                # Reset delay on successful requests
                self.delays[host] = self.initial_delay
                return self.initial_delay
            elif was_rate_limited:
                # Increase delay for rate-limited requests
                current = self.delays.get(host, self.initial_delay)
                new_delay = min(current + self.backoff_step, self.max_delay)
                self.delays[host] = new_delay
                return new_delay
            else:
                # Keep current delay for other errors
                return self.delays.get(host, self.initial_delay)
    
    def process_response(self, host: str, status_code: Optional[int] = None, error: Optional[Exception] = None) -> float:
        """
        Process an API response and adjust delay based on the result.
        
        Args:
            host (str): The host/endpoint identifier.
            status_code (int, optional): HTTP status code from the response.
            error (Exception, optional): Any exception that occurred during the request.
            
        Returns:
            float: The current delay for this host.
        """
        success = False
        rate_limited = False
        
        if error is not None:
            # Check if the error is related to rate limiting
            error_str = str(error).lower()
            rate_limited = "429" in error_str or "too many requests" in error_str
        elif status_code is not None:
            # Check if the response was successful
            success = 200 <= status_code < 300
            # Check if the response indicates rate limiting
            rate_limited = status_code == 429
            
        return self.handle_request(host, success, rate_limited)

# Create a global instance for use across the application
global_rate_limiter = RateLimiter()

# Add a utility method to the global instance for easy access
def process_response(host: str, status_code: Optional[int] = None, error: Optional[Exception] = None) -> float:
    """Convenience function to access the global rate limiter's process_response method."""
    return global_rate_limiter.process_response(host, status_code, error)
