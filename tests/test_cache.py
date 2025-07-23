import time
import pytest
from manifold_core.utils.cache import SecretCache, cached_has_secret
from manifold_core.secrets.dotenv.backend import Backend


class MockSecretBackend:
    """Mock secret backend for testing"""
    def __init__(self):
        self.secrets = {}
        self.call_count = 0
    
    def has_secret(self, key: str) -> bool:
        self.call_count += 1
        return key in self.secrets
    
    def set_secret(self, key: str, value: str):
        self.secrets[key] = value


def test_secret_cache_basic():
    """Test basic cache functionality"""
    cache = SecretCache(ttl_seconds=1)
    
    # Test setting and getting
    cache.set("test_key", True)
    assert cache.get("test_key") == True
    
    # Test non-existent key
    assert cache.get("non_existent") is None


def test_secret_cache_expiration():
    """Test cache expiration"""
    cache = SecretCache(ttl_seconds=0.1)  # Very short TTL for testing
    
    cache.set("test_key", True)
    assert cache.get("test_key") == True
    
    # Wait for expiration
    time.sleep(0.2)
    assert cache.get("test_key") is None


def test_cached_has_secret():
    """Test the cached_has_secret function"""
    mock_backend = MockSecretBackend()
    mock_backend.secrets["test_key"] = "value"
    
    # First call should hit the backend
    result1 = cached_has_secret(mock_backend, "test_key")
    assert result1 == True
    assert mock_backend.call_count == 1
    
    # Second call should use cache
    result2 = cached_has_secret(mock_backend, "test_key")
    assert result2 == True
    assert mock_backend.call_count == 1  # Should not have increased
    
    # Test non-existent key
    result3 = cached_has_secret(mock_backend, "non_existent")
    assert result3 == False
    assert mock_backend.call_count == 2  # Should have increased for new key


def test_cache_invalidation():
    """Test cache invalidation"""
    cache = SecretCache()
    
    cache.set("test_key", True)
    assert cache.get("test_key") == True
    
    cache.invalidate("test_key")
    assert cache.get("test_key") is None


def test_cache_clear():
    """Test cache clearing"""
    cache = SecretCache()
    
    cache.set("key1", True)
    cache.set("key2", False)
    assert len(cache.cache) == 2
    
    cache.clear()
    assert len(cache.cache) == 0


def test_cache_cleanup_expired():
    """Test cleanup of expired entries"""
    cache = SecretCache(ttl_seconds=0.1)
    
    cache.set("key1", True)
    cache.set("key2", False)
    assert len(cache.cache) == 2
    
    # Wait for expiration
    time.sleep(0.2)
    
    cache.cleanup_expired()
    assert len(cache.cache) == 0 