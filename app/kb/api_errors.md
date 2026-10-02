# API Errors and Request Failures

For API errors, collect the endpoint, HTTP status code, request ID, timestamp with timezone, and a minimal sanitized request example. A 401 usually indicates missing or invalid authentication. A 403 indicates the credential is recognized but lacks permission. A 429 indicates rate limiting.

For repeated 5xx errors, ask whether failures affect all requests or only a subset, capture request IDs, and route to Engineering when the issue is reproducible or materially blocks production traffic.
