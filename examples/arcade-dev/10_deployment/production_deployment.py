#!/usr/bin/env python3
"""
Production Deployment Example for Arcade.dev Integration

This example demonstrates production-ready deployment of Arcade.dev integration including:
- Initialization and bootstrapping
- Configuration management
- Health checks and readiness probes
- Graceful shutdown
- Resource management and cleanup
"""

import os
import sys
import asyncio
import signal
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import time
import json
import yaml
from contextlib import asynccontextmanager
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess
import psutil

# Setup FACT imports using the import helper
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.import_helper import setup_fact_imports

# Setup FACT module path
setup_fact_imports()

from src.core.driver import FACTDriver
from src.core.config import Config
from src.cache.manager import CacheManager
from src.monitoring.metrics import MetricsCollector
from src.security.auth import SecurityManager
from src.core.errors import ConfigurationError, ServiceStartupError


@dataclass
class ServiceHealthStatus:
    """Health status of a service component."""
    service_name: str
    healthy: bool
    last_check: float
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class DeploymentConfig:
    """Production deployment configuration."""
    # Service configuration
    service_name: str = "fact-arcade-integration"
    service_version: str = "1.0.0"
    environment: str = "production"
    
    # Network configuration
    host: str = "0.0.0.0"
    port: int = 8080
    health_check_port: int = 8081
    
    # Arcade.dev configuration
    arcade_api_key: str = ""
    arcade_api_url: str = "https://api.arcade.dev"
    arcade_timeout: int = 30
    arcade_max_retries: int = 3
    
    # Cache configuration
    cache_backend: str = "redis"
    cache_host: str = "localhost"
    cache_port: int = 6379
    cache_db: int = 0
    
    # Monitoring configuration
    metrics_enabled: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    
    # Performance configuration
    worker_threads: int = 4
    max_concurrent_requests: int = 100
    request_timeout: int = 60
    
    # Security configuration
    enable_auth: bool = True
    jwt_secret: str = ""
    cors_origins: List[str] = field(default_factory=list)


class ProductionArcadeService:
    """Production-ready Arcade.dev integration service."""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Core components
        self.driver: Optional[FACTDriver] = None
        self.cache_manager: Optional[CacheManager] = None
        self.arcade_client: Optional[ArcadeClient] = None
        self.arcade_gateway: Optional[ArcadeGateway] = None
        self.metrics: Optional[MetricsCollector] = None
        self.security_manager: Optional[SecurityManager] = None
        
        # Service state
        self.is_running = False
        self.is_ready = False
        self.startup_time: Optional[float] = None
        self.shutdown_event = asyncio.Event()
        self.health_status: Dict[str, ServiceHealthStatus] = {}
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.thread_pool = ThreadPoolExecutor(max_workers=config.worker_threads)
        
        # Signal handlers
        self._setup_signal_handlers()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up production logging configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'/var/log/{self.config.service_name}.log')
            ]
        )
        
        logger = logging.getLogger(self.config.service_name)
        logger.info(f"Initializing {self.config.service_name} v{self.config.service_version}")
        return logger
        
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
    async def initialize(self):
        """Initialize all service components."""
        self.logger.info("Starting service initialization")
        initialization_start = time.time()
        
        try:
            # Load and validate configuration
            await self._load_configuration()
            
            # Initialize core components
            await self._initialize_cache()
            await self._initialize_arcade_client()
            await self._initialize_monitoring()
            await self._initialize_security()
            await self._initialize_gateway()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Perform initial health checks
            await self._perform_initial_health_checks()
            
            self.startup_time = time.time() - initialization_start
            self.is_running = True
            self.is_ready = True
            
            self.logger.info(f"Service initialization completed in {self.startup_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            await self.cleanup()
            raise ServiceStartupError(f"Failed to initialize service: {e}")
            
    async def _load_configuration(self):
        """Load and validate configuration from environment and files."""
        self.logger.info("Loading configuration")
        
        # Load from environment variables
        self.config.arcade_api_key = os.getenv("ARCADE_API_KEY", self.config.arcade_api_key)
        self.config.arcade_api_url = os.getenv("ARCADE_API_URL", self.config.arcade_api_url)
        self.config.cache_host = os.getenv("CACHE_HOST", self.config.cache_host)
        self.config.jwt_secret = os.getenv("JWT_SECRET", self.config.jwt_secret)
        
        # Load from configuration file if exists
        config_file = os.getenv("CONFIG_FILE", "/etc/fact-arcade/config.yaml")
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                self._merge_config(file_config)
                
        # Validate required configuration
        if not self.config.arcade_api_key:
            raise ConfigurationError("ARCADE_API_KEY is required")
            
        if self.config.enable_auth and not self.config.jwt_secret:
            raise ConfigurationError("JWT_SECRET is required when authentication is enabled")
            
        self.logger.info("Configuration loaded and validated")
        
    def _merge_config(self, file_config: Dict[str, Any]):
        """Merge file configuration with current config."""
        for key, value in file_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                
    async def _initialize_cache(self):
        """Initialize cache manager."""
        self.logger.info("Initializing cache manager")
        
        cache_config = {
            "backend": self.config.cache_backend,
            "host": self.config.cache_host,
            "port": self.config.cache_port,
            "db": self.config.cache_db
        }
        
        self.cache_manager = CacheManager(cache_config)
        await self.cache_manager.initialize()
        
        # Test cache connectivity
        test_key = "health_check_cache"
        await self.cache_manager.set(test_key, {"status": "ok"}, ttl=60)
        result = await self.cache_manager.get(test_key)
        
        if not result:
            raise ServiceStartupError("Cache connectivity test failed")
            
        await self.cache_manager.delete(test_key)
        self.logger.info("Cache manager initialized successfully")
        
    async def _initialize_arcade_client(self):
        """Initialize Arcade.dev client."""
        self.logger.info("Initializing Arcade.dev client")
        
        self.arcade_client = ArcadeClient(
            api_key=self.config.arcade_api_key,
            api_url=self.config.arcade_api_url,
            timeout=self.config.arcade_timeout,
            max_retries=self.config.arcade_max_retries,
            cache_manager=self.cache_manager
        )
        
        await self.arcade_client.connect()
        
        # Test API connectivity
        try:
            health_result = await self.arcade_client.health_check()
            self.logger.info(f"Arcade.dev API health: {health_result.get('status', 'unknown')}")
        except Exception as e:
            self.logger.warning(f"Arcade.dev API health check failed: {e}")
            
        self.logger.info("Arcade.dev client initialized successfully")
        
    async def _initialize_monitoring(self):
        """Initialize monitoring and metrics collection."""
        if not self.config.metrics_enabled:
            self.logger.info("Metrics collection disabled")
            return
            
        self.logger.info("Initializing metrics collection")
        
        self.metrics = MetricsCollector(
            service_name=self.config.service_name,
            service_version=self.config.service_version,
            port=self.config.metrics_port
        )
        
        await self.metrics.initialize()
        
        # Register custom metrics
        await self._register_custom_metrics()
        
        self.logger.info("Metrics collection initialized successfully")
        
    async def _register_custom_metrics(self):
        """Register custom application metrics."""
        if not self.metrics:
            return
            
        # Service metrics
        await self.metrics.register_gauge("service_uptime_seconds", "Service uptime in seconds")
        await self.metrics.register_counter("requests_total", "Total number of requests", ["method", "status"])
        await self.metrics.register_histogram("request_duration_seconds", "Request duration in seconds")
        
        # Arcade.dev metrics
        await self.metrics.register_counter("arcade_requests_total", "Total Arcade.dev API requests", ["endpoint", "status"])
        await self.metrics.register_histogram("arcade_request_duration_seconds", "Arcade.dev request duration")
        
        # Cache metrics
        await self.metrics.register_counter("cache_operations_total", "Total cache operations", ["operation", "result"])
        
    async def _initialize_security(self):
        """Initialize security manager."""
        if not self.config.enable_auth:
            self.logger.info("Authentication disabled")
            return
            
        self.logger.info("Initializing security manager")
        
        self.security_manager = SecurityManager(
            jwt_secret=self.config.jwt_secret,
            cors_origins=self.config.cors_origins
        )
        
        await self.security_manager.initialize()
        self.logger.info("Security manager initialized successfully")
        
    async def _initialize_gateway(self):
        """Initialize Arcade.dev gateway."""
        self.logger.info("Initializing Arcade.dev gateway")
        
        self.arcade_gateway = ArcadeGateway(
            arcade_client=self.arcade_client,
            cache_manager=self.cache_manager,
            metrics=self.metrics,
            security_manager=self.security_manager
        )
        
        await self.arcade_gateway.initialize()
        self.logger.info("Arcade.dev gateway initialized successfully")
        
    async def _start_background_tasks(self):
        """Start background maintenance tasks."""
        self.logger.info("Starting background tasks")
        
        # Health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self.background_tasks.append(health_task)
        
        # Metrics collection task
        if self.metrics:
            metrics_task = asyncio.create_task(self._metrics_collection_loop())
            self.background_tasks.append(metrics_task)
            
        # Cache cleanup task
        if self.cache_manager:
            cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
            self.background_tasks.append(cleanup_task)
            
        self.logger.info(f"Started {len(self.background_tasks)} background tasks")
        
    async def _perform_initial_health_checks(self):
        """Perform initial health checks on all components."""
        self.logger.info("Performing initial health checks")
        
        # Check all components
        await self._check_cache_health()
        await self._check_arcade_health()
        await self._check_system_health()
        
        # Verify all components are healthy
        unhealthy_services = [
            name for name, status in self.health_status.items()
            if not status.healthy
        ]
        
        if unhealthy_services:
            raise ServiceStartupError(f"Unhealthy services: {unhealthy_services}")
            
        self.logger.info("All initial health checks passed")
        
    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while not self.shutdown_event.is_set():
            try:
                await self._check_cache_health()
                await self._check_arcade_health()
                await self._check_system_health()
                
                # Wait for next check
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=30.0  # Check every 30 seconds
                )
                
            except asyncio.TimeoutError:
                continue  # Continue health checks
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(30)
                
    async def _check_cache_health(self):
        """Check cache health."""
        try:
            start_time = time.time()
            test_key = f"health_check_{int(time.time())}"
            
            await self.cache_manager.set(test_key, "ok", ttl=60)
            result = await self.cache_manager.get(test_key)
            await self.cache_manager.delete(test_key)
            
            response_time = time.time() - start_time
            
            self.health_status["cache"] = ServiceHealthStatus(
                service_name="cache",
                healthy=result == "ok",
                last_check=time.time(),
                details={"response_time": response_time}
            )
            
        except Exception as e:
            self.health_status["cache"] = ServiceHealthStatus(
                service_name="cache",
                healthy=False,
                last_check=time.time(),
                error_message=str(e)
            )
            
    async def _check_arcade_health(self):
        """Check Arcade.dev API health."""
        try:
            start_time = time.time()
            result = await self.arcade_client.health_check()
            response_time = time.time() - start_time
            
            self.health_status["arcade"] = ServiceHealthStatus(
                service_name="arcade",
                healthy=result.get("status") == "healthy",
                last_check=time.time(),
                details={"response_time": response_time, "api_status": result}
            )
            
        except Exception as e:
            self.health_status["arcade"] = ServiceHealthStatus(
                service_name="arcade",
                healthy=False,
                last_check=time.time(),
                error_message=str(e)
            )
            
    async def _check_system_health(self):
        """Check system resource health."""
        try:
            # Check memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()
            
            # Check if we're using too much memory (> 1GB as example)
            memory_mb = memory_info.rss / 1024 / 1024
            healthy = memory_mb < 1024 and cpu_percent < 80
            
            self.health_status["system"] = ServiceHealthStatus(
                service_name="system",
                healthy=healthy,
                last_check=time.time(),
                details={
                    "memory_mb": memory_mb,
                    "cpu_percent": cpu_percent,
                    "uptime": time.time() - self.startup_time if self.startup_time else 0
                }
            )
            
        except Exception as e:
            self.health_status["system"] = ServiceHealthStatus(
                service_name="system",
                healthy=False,
                last_check=time.time(),
                error_message=str(e)
            )
            
    async def _metrics_collection_loop(self):
        """Background task for metrics collection."""
        while not self.shutdown_event.is_set():
            try:
                if self.metrics and self.startup_time:
                    uptime = time.time() - self.startup_time
                    await self.metrics.record_gauge("service_uptime_seconds", uptime)
                    
                # Wait for next collection
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=60.0  # Collect every minute
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
                
    async def _cache_cleanup_loop(self):
        """Background task for cache cleanup."""
        while not self.shutdown_event.is_set():
            try:
                if self.cache_manager:
                    await self.cache_manager.cleanup_expired()
                    
                # Wait for next cleanup
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=300.0  # Cleanup every 5 minutes
                )
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(300)
                
    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all components."""
        overall_healthy = all(
            status.healthy for status in self.health_status.values()
        )
        
        return {
            "service": self.config.service_name,
            "version": self.config.service_version,
            "environment": self.config.environment,
            "status": "healthy" if overall_healthy else "unhealthy",
            "uptime": time.time() - self.startup_time if self.startup_time else 0,
            "components": {
                name: {
                    "healthy": status.healthy,
                    "last_check": status.last_check,
                    "details": status.details,
                    "error": status.error_message
                }
                for name, status in self.health_status.items()
            }
        }
        
    async def get_readiness_status(self) -> Dict[str, Any]:
        """Get readiness status for load balancer probes."""
        return {
            "ready": self.is_ready,
            "startup_time": self.startup_time,
            "components_ready": len(self.health_status) > 0
        }
        
    async def shutdown(self):
        """Gracefully shutdown the service."""
        if not self.is_running:
            return
            
        self.logger.info("Starting graceful shutdown")
        shutdown_start = time.time()
        
        # Set shutdown event
        self.shutdown_event.set()
        self.is_ready = False
        
        try:
            # Cancel background tasks
            self.logger.info("Cancelling background tasks")
            for task in self.background_tasks:
                task.cancel()
                
            # Wait for tasks to complete
            if self.background_tasks:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
                
            # Cleanup components
            await self.cleanup()
            
            shutdown_time = time.time() - shutdown_start
            self.logger.info(f"Graceful shutdown completed in {shutdown_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
        finally:
            self.is_running = False
            
    async def cleanup(self):
        """Clean up all resources."""
        self.logger.info("Cleaning up resources")
        
        # Close gateway
        if self.arcade_gateway:
            await self.arcade_gateway.cleanup()
            
        # Close arcade client
        if self.arcade_client:
            await self.arcade_client.disconnect()
            
        # Close cache manager
        if self.cache_manager:
            await self.cache_manager.close()
            
        # Close metrics collector
        if self.metrics:
            await self.metrics.cleanup()
            
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("Resource cleanup completed")


async def create_health_check_server(service: ProductionArcadeService):
    """Create HTTP server for health checks."""
    from aiohttp import web, web_response
    
    async def health_handler(request):
        """Health check endpoint."""
        status = await service.get_health_status()
        status_code = 200 if status["status"] == "healthy" else 503
        return web_response.json_response(status, status=status_code)
        
    async def readiness_handler(request):
        """Readiness check endpoint."""
        status = await service.get_readiness_status()
        status_code = 200 if status["ready"] else 503
        return web_response.json_response(status, status=status_code)
        
    app = web.Application()
    app.router.add_get('/health', health_handler)
    app.router.add_get('/ready', readiness_handler)
    
    return app


async def main():
    """Main service entry point."""
    # Load configuration
    config = DeploymentConfig()
    
    # Override from environment
    config.environment = os.getenv("ENVIRONMENT", config.environment)
    config.log_level = os.getenv("LOG_LEVEL", config.log_level)
    config.port = int(os.getenv("PORT", str(config.port)))
    
    # Create and start service
    service = ProductionArcadeService(config)
    
    try:
        # Initialize service
        await service.initialize()
        
        # Create health check server
        health_app = await create_health_check_server(service)
        
        # Start health check server
        from aiohttp import web
        health_runner = web.AppRunner(health_app)
        await health_runner.setup()
        health_site = web.TCPSite(
            health_runner, 
            service.config.host, 
            service.config.health_check_port
        )
        await health_site.start()
        
        service.logger.info(f"Health check server started on port {service.config.health_check_port}")
        service.logger.info(f"Service ready and accepting requests")
        
        # Wait for shutdown signal
        await service.shutdown_event.wait()
        
        # Cleanup health server
        await health_runner.cleanup()
        
        service.logger.info("Service shutdown completed")
        return 0
        
    except Exception as e:
        if service:
            service.logger.error(f"Service failed: {e}")
        else:
            print(f"Service startup failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)