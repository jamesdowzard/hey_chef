"""
Base service classes for Hey Chef v2 backend.
Provides common patterns for async services with proper error handling and logging.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager


class BaseService(ABC):
    """
    Base class for all services in Hey Chef v2.
    
    Provides common functionality like:
    - Logging setup
    - Resource management
    - Error handling patterns
    - Async context management
    """
    
    def __init__(self, service_name: str):
        """
        Initialize base service.
        
        Args:
            service_name: Name of the service for logging purposes
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"hey_chef.services.{service_name}")
        self._initialized = False
        self._resources: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """
        Initialize the service.
        Override this method to add custom initialization logic.
        """
        if self._initialized:
            return
            
        self.logger.info(f"Initializing {self.service_name} service")
        try:
            await self._initialize_impl()
            self._initialized = True
            self.logger.info(f"{self.service_name} service initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.service_name} service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """
        Clean up service resources.
        Override this method to add custom cleanup logic.
        """
        if not self._initialized:
            return
            
        self.logger.info(f"Cleaning up {self.service_name} service")
        try:
            await self._cleanup_impl()
            self._resources.clear()
            self._initialized = False
            self.logger.info(f"{self.service_name} service cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Error during {self.service_name} service cleanup: {e}")
            # Don't re-raise cleanup errors
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """
        Service-specific initialization logic.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    async def _cleanup_impl(self) -> None:
        """
        Service-specific cleanup logic.
        Must be implemented by subclasses.
        """
        pass
    
    def _store_resource(self, name: str, resource: Any) -> None:
        """
        Store a resource for later cleanup.
        
        Args:
            name: Resource name
            resource: Resource object
        """
        self._resources[name] = resource
    
    def _get_resource(self, name: str) -> Optional[Any]:
        """
        Get a stored resource.
        
        Args:
            name: Resource name
            
        Returns:
            Resource object or None if not found
        """
        return self._resources.get(name)
    
    @asynccontextmanager
    async def managed_operation(self, operation_name: str):
        """
        Context manager for logging and error handling of operations.
        
        Args:
            operation_name: Name of the operation for logging
        """
        self.logger.debug(f"Starting {operation_name}")
        try:
            yield
            self.logger.debug(f"Completed {operation_name}")
        except Exception as e:
            self.logger.error(f"Error in {operation_name}: {e}")
            raise
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


class AudioService(BaseService):
    """
    Base class for audio-related services.
    Provides common audio functionality and error handling.
    """
    
    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.is_active = False
        self._stop_event: Optional[asyncio.Event] = None
    
    async def start(self) -> None:
        """Start the audio service."""
        if not self._initialized:
            await self.initialize()
        
        if self.is_active:
            self.logger.warning(f"{self.service_name} service is already active")
            return
        
        self.logger.info(f"Starting {self.service_name} service")
        self._stop_event = asyncio.Event()
        self.is_active = True
        await self._start_impl()
    
    async def stop(self) -> None:
        """Stop the audio service."""
        if not self.is_active:
            return
        
        self.logger.info(f"Stopping {self.service_name} service")
        self.is_active = False
        
        if self._stop_event:
            self._stop_event.set()
        
        await self._stop_impl()
        self._stop_event = None
    
    @abstractmethod
    async def _start_impl(self) -> None:
        """Service-specific start logic."""
        pass
    
    @abstractmethod
    async def _stop_impl(self) -> None:
        """Service-specific stop logic."""
        pass
    
    def _should_stop(self) -> bool:
        """Check if the service should stop."""
        return self._stop_event is not None and self._stop_event.is_set()
    
    async def _cleanup_impl(self) -> None:
        """Clean up audio service resources."""
        if self.is_active:
            await self.stop()