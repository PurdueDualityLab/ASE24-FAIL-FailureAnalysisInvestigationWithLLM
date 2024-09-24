from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
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

# View for individual incident detail page
def incident_detail_view(request, pk):
    # Fetch the incident by primary key, or return 404 if not found
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, 'articles/incident_detail.html', {'incident': incident})