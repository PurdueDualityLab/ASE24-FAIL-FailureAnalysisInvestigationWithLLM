from django.shortcuts import render
from .models import Incident

def index(request):
    return render(
        request,
        "articles/index.html",
        {
            "incidents": Incident.objects.all(),
        },
    )

#user front view
def public_page(request):
    incidents = Incident.objects.prefetch_related('articles').all()  # Fetch incidents with related articles
    return render(request, 'articles/public_page.html', {'incidents': incidents})
