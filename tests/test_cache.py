from app.core.cache import (
    get_cache,
    set_cache,
    delete_cache
)

key = "test:cache"

data = {
    "id": 1,
    "title": "Learn Redis"
}

# Store
print(set_cache(key, data, ttl=60))

# Retrieve
print(get_cache(key))

# Delete
print(delete_cache(key))

# Retrieve again
print(get_cache(key))