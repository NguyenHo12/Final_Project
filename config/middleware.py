from django.shortcuts import redirect
from django.urls import reverse

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require authentication
        public_urls = [
            reverse('login'),
            '/admin/login/',
            '/static/',
            '/media/',
        ]

        # Check if the current path is a public URL
        if not any(request.path.startswith(url) for url in public_urls):
            # If user is not authenticated, redirect to login page
            if not request.user.is_authenticated:
                return redirect('login')

        response = self.get_response(request)
        return response 