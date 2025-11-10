# Spotify API Configuration
# Get these values from: https://developer.spotify.com/dashboard

# Required: Your Spotify App Credentials
CLIENT_ID = 'd94e5396495e422bbad704a1ac5c0dee'
CLIENT_SECRET = 'e97011311bf747e1b51a54a9b8079bc5'
REDIRECT_URI = 'https://developer.spotify.com/documentation/web-api'

# Optional: Application Settings
DEFAULT_BATCH_SIZE = 20  # Number of songs to process at once
DEFAULT_DELAY = 0.5      # Seconds to wait between API calls
ERROR_RETRY_DELAY = 60   # Seconds to wait after an error

# Spotify API Scopes (don't change unless you know what you're doing)
SCOPES = "user-library-read user-top-read user-library-modify"

# Time range options for top tracks
TIME_RANGES = {
    'short': 'short_term',    # Last 4 weeks
    'medium': 'medium_term',  # Last 6 months  
    'long': 'long_term'       # Several years
}