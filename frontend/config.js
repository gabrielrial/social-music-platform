// Where the API lives.
// - Served by the API itself (http://localhost:8000/app, or through ngrok):
//   same origin, so the calls go to wherever the page came from.
// - Served by `make front` on :8080: the API is on localhost:8000, allowed by
//   the default CORS_ORIGINS.
window.RATE_API = location.port === "8080" ? "http://localhost:8000" : location.origin;
