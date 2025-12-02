class MapboxCSPMiddleware:
    """
    Middleware para permitir que o Mapbox funcione
    Remove restrições de Content Security Policy
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Remove CSP existente
        for header in ['Content-Security-Policy', 'X-Content-Security-Policy']:
            if header in response:
                del response[header]
        
        return response