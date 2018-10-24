# IIIF endpoint for all collections
IIIF_UNIVERSE_COLLECTION_URL = 'http://ryanfb.github.io/iiif-universe/iiif-universe.json' 

# Call rate limit (per second) - Avoid overwhelming remote servers
API_CALLS_LIMIT_PER_SECONDS = 1

# HTTP request timeout after x number of seconds - Prevents hanging requests
HTTP_REQUEST_TIMEOUT = 5  

# Max call depth for collections
MAX_SUB_COLLECTIONS_DEPTH = 10