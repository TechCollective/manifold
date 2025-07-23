# Secret Cache System

## Overview

The Manifold system now includes a caching layer for secret existence checks to improve performance. This addresses the performance issue where every page load would trigger multiple expensive secret backend calls (especially with Bitwarden) to check if credentials exist for integrations.

## Problem Solved

Previously, every time the sidebar was rendered, the system would:
1. Call `list_unifi_servers()` → check username/password for each server
2. Call `list_slack_integrations()` → check token for each integration  
3. Call `list_autotask_integrations()` → check username/secret for each integration

Each `has_secret()` call in Bitwarden makes a subprocess call to `bws secret list`, which is expensive and causes noticeable lag.

## Solution

The new caching system:
- Caches secret existence results for 1 hour (configurable)
- Uses thread-safe operations with locks
- Automatically invalidates cache when secrets are modified
- Provides CLI tools for cache management

## Architecture

### Core Components

1. **SecretCache Class** (`src/manifold_core/utils/cache.py`)
   - Thread-safe in-memory cache with TTL
   - Automatic expiration handling
   - Cache invalidation methods

2. **cached_has_secret() Function**
   - Wrapper around backend `has_secret()` calls
   - Checks cache first, falls back to backend
   - Handles exceptions gracefully

3. **Cache Invalidation**
   - Automatically invalidates relevant cache entries when secrets are modified
   - Integrated into all secret set/delete operations

### Integration Points

The caching system is integrated into:

- **UniFi**: `list_unifi_servers()` now uses cached checks for username/password
- **Slack**: `list_slack_integrations()` now uses cached checks for tokens  
- **Autotask**: `list_autotask_integrations()` now uses cached checks for username/secret

## Usage

### Automatic Usage

The caching is transparent to the application. All existing code continues to work, but now with improved performance.

### Manual Cache Management

Use the CLI commands to manage the cache:

```bash
# Check cache status
python -m manifold_cli cache status

# Clear all cached entries
python -m manifold_cli cache clear

# Remove expired entries
python -m manifold_cli cache cleanup

# Invalidate specific secret
python -m manifold_cli cache invalidate "unifi:server1:username"
```

### Cache Statistics

The cache status command shows:
- Total cached entries
- TTL configuration
- Individual entry details (key, exists, age)

## Configuration

### TTL (Time To Live)

Default TTL is 1 hour (3600 seconds). This can be modified by changing the `ttl_seconds` parameter in the `SecretCache` constructor.

### Backend Compatibility

The caching system works with all secret backends:
- **Dotenv**: Checks environment variable existence
- **Bitwarden**: Caches the expensive `bws secret list` calls

## Performance Impact

### Before Caching
- Each page load: 2-6+ backend calls per integration
- Bitwarden: Each call = subprocess execution
- Noticeable lag on sidebar rendering

### After Caching
- First page load: Same as before (cache miss)
- Subsequent page loads: 0 backend calls (cache hit)
- Cache expires after 1 hour, then refreshes
- Significant performance improvement

## Cache Invalidation Strategy

The cache is automatically invalidated when:

1. **Credentials are set/updated**:
   - `set_unifi_credentials()` → invalidates username/password cache
   - `set_slack_token()` → invalidates token cache
   - `set_autotask_credentials()` → invalidates username/secret cache

2. **Integrations are deleted**:
   - `delete_unifi_server()` → invalidates credentials cache
   - `delete_slack_integration()` → invalidates token cache
   - `delete_autotask_integration()` → invalidates credentials cache

3. **Manual invalidation**:
   - CLI commands for debugging/maintenance
   - Direct cache manipulation if needed

## Testing

Run the cache tests to verify functionality:

```bash
pytest tests/test_cache.py
```

Tests cover:
- Basic cache operations
- TTL expiration
- Cache invalidation
- Thread safety
- Integration with secret backends

## Monitoring

Monitor cache effectiveness:

```bash
# Check cache hit rates and usage
python -m manifold_cli cache status

# Look for patterns in cache misses
# High miss rates might indicate need for longer TTL
```

## Troubleshooting

### Cache Not Working
1. Verify backend has `has_secret()` method implemented
2. Check for exceptions in cache operations
3. Use CLI status command to inspect cache state

### Performance Still Poor
1. Check if cache is being invalidated too frequently
2. Consider increasing TTL if data doesn't change often
3. Monitor cache hit rates

### Memory Usage
1. Cache is in-memory only, entries expire automatically
2. Use cleanup command to remove expired entries
3. Monitor cache size with status command

## Future Enhancements

Potential improvements:
- Persistent cache storage (Redis, file-based)
- Configurable TTL per secret type
- Cache warming strategies
- Metrics and monitoring integration
- Distributed cache for multi-instance deployments 