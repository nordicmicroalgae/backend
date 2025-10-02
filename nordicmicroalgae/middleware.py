class CorsMiddleware:
    enabled_paths = ("/api/",)

    exposed_headers = (
        "X-Total",  # custom header used in REST API
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if any(request.path_info.startswith(path) for path in self.enabled_paths):
            response["Access-Control-Allow-Origin"] = "*"

            # extends the default CORS-safelist
            response["Access-Control-Expose-Headers"] = ", ".join(self.exposed_headers)

        return response
