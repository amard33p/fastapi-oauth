from app.config import settings
from httpx_oauth.clients.google import GoogleOAuth2

# Add more providers (e.g., GitHub) here later as needed

google_oauth_client = GoogleOAuth2(
    settings.GOOGLE_CLIENT_ID,
    settings.GOOGLE_CLIENT_SECRET,
)
