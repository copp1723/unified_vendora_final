"""
VENDORA Reliability Module
Provides circuit breaker and fault tolerance patterns
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, circuit_breaker, circuit_manager, CircuitBreakerOpenError

__all__ = ['CircuitBreaker', 'CircuitBreakerConfig', 'circuit_breaker', 'circuit_manager', 'CircuitBreakerOpenError']