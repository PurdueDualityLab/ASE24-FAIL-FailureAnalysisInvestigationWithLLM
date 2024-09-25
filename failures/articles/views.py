from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Incident
from django.utils.dateparse import parse_date  # Import parse_date

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
    query = request.GET.get('q', '')  # Get the query from the request
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    
    incidents = Incident.objects.all()

    if query:  # If there's a search query, filter incidents by title
        incidents = incidents.filter(title__icontains=query)

    if start_date:  # Filter by start date
        start_date_parsed = parse_date(start_date)
        if start_date_parsed:
            incidents = incidents.filter(published__gte=start_date_parsed)

    if end_date:  # Filter by end date
        end_date_parsed = parse_date(end_date)
        if end_date_parsed:
            incidents = incidents.filter(published__lte=end_date_parsed)

    context = {
        'incidents': incidents,
    }
    
    return render(request, 'articles/public_page.html', context)

# View for individual incident detail page
def incident_detail_view(request, pk):
    # Fetch the incident by primary key, or return 404 if not found
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, 'articles/incident_detail.html', {'incident': incident})