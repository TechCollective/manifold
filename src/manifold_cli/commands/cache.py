import typer
from rich import print
from rich.table import Table
from manifold_core.utils.cache import get_secret_cache

cache_app = typer.Typer(help="Manage secret cache")

@cache_app.command("status")
def cache_status():
    """Show cache status and statistics"""
    cache = get_secret_cache()
    
    # Get cache statistics
    total_entries = len(cache.cache)
    print(f"Cache Status:")
    print(f"  Total entries: {total_entries}")
    print(f"  TTL: {cache.ttl_seconds} seconds ({cache.ttl_seconds / 3600:.1f} hours)")
    
    if total_entries > 0:
        print(f"\nCached entries:")
        table = Table()
        table.add_column("Secret Key")
        table.add_column("Exists")
        table.add_column("Age (seconds)")
        
        import time
        current_time = time.time()
        
        for key, (exists, timestamp) in cache.cache.items():
            age = current_time - timestamp
            table.add_row(key, "✅" if exists else "❌", f"{age:.0f}")
        
        print(table)

@cache_app.command("clear")
def clear_cache():
    """Clear all cached entries"""
    cache = get_secret_cache()
    cache.clear()
    print("✅ Cache cleared")

@cache_app.command("cleanup")
def cleanup_cache():
    """Remove expired entries from cache"""
    cache = get_secret_cache()
    before_count = len(cache.cache)
    cache.cleanup_expired()
    after_count = len(cache.cache)
    removed = before_count - after_count
    print(f"✅ Removed {removed} expired entries from cache")
    print(f"   Remaining entries: {after_count}")

@cache_app.command("invalidate")
def invalidate_secret(key: str):
    """Invalidate a specific secret key from cache"""
    cache = get_secret_cache()
    cache.invalidate(key)
    print(f"✅ Invalidated cache entry for: {key}") 