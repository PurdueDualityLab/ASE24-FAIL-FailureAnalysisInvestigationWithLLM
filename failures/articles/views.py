from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from .models import Incident
from django.utils.dateparse import parse_date  # Import parse_date
from django.db.models import Count

def index(request):
    return render(
        request,
        "articles/index.html",
        {
            "incidents": Incident.objects.all(),
        },
    )


# User front view
def public_page(request):
    query = request.GET.get('q', '')  # Get the search query
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort_by_articles = request.GET.get('sort', '')  # Get sort parameter

    # Get selected values for each filter
    dimension_options_selected = request.GET.getlist('dimension_option')
    phase_options_selected = request.GET.getlist('phase_option')
    boundary_options_selected = request.GET.getlist('boundary_option')
    recurring_options_selected = request.GET.getlist('recurring_option')
    nature_options_selected = request.GET.getlist('nature_option')
    intent_options_selected = request.GET.getlist('intent_option')
    objective_options_selected = request.GET.getlist('objective_option')
    capability_options_selected = request.GET.getlist('capability_option')
    duration_options_selected = request.GET.getlist('duration_option')
    behaviour_options_selected = request.GET.getlist('behaviour_option')
    
    # Get all distinct options for each filter category
    dimension_options = Incident.objects.values_list('dimension_option', flat=True).distinct()
    phase_options = Incident.objects.values_list('phase_option', flat=True).distinct()
    boundary_options = Incident.objects.values_list('boundary_option', flat=True).distinct()
    recurring_options = Incident.objects.values_list('recurring_option', flat=True).distinct()
    nature_options = Incident.objects.values_list('nature_option', flat=True).distinct()
    intent_options = Incident.objects.values_list('intent_option', flat=True).distinct()
    objective_options = Incident.objects.values_list('objective_option', flat=True).distinct()
    capability_options = Incident.objects.values_list('capability_option', flat=True).distinct()
    duration_options = Incident.objects.values_list('duration_option', flat=True).distinct()
    behaviour_options = Incident.objects.values_list('behaviour_option', flat=True).distinct()
    # Annotate incidents with the count of related articles
    incidents = Incident.objects.annotate(article_count=Count('articles'))

    # Apply filters
    if query:
        incidents = incidents.filter(title__icontains=query)

    if start_date:
        incidents = incidents.filter(published__gte=start_date)

    if end_date:
        incidents = incidents.filter(published__lte=end_date)

    if dimension_options_selected:
        incidents = incidents.filter(dimension_option__in=dimension_options_selected)

    if phase_options_selected:
        incidents = incidents.filter(phase_option__in=phase_options_selected)

    if boundary_options_selected:
        incidents = incidents.filter(boundary_option__in=boundary_options_selected)

    if recurring_options_selected:
        incidents = incidents.filter(recurring_option__in=recurring_options_selected)

    if nature_options_selected:
        incidents = incidents.filter(nature_option__in=nature_options_selected)

    if intent_options_selected:
        incidents = incidents.filter(intent_option__in=intent_options_selected)

    if objective_options_selected:
        incidents = incidents.filter(objective_option__in=objective_options_selected)

    if capability_options_selected:
        incidents = incidents.filter(capability_option__in=capability_options_selected)

    if duration_options_selected:
        incidents = incidents.filter(duration_option__in=duration_options_selected)

    if behaviour_options_selected:
        incidents = incidents.filter(behavior_option__in=behaviour_options_selected)

    # Sorting logic
    if sort_by_articles == 'asc':
        incidents = incidents.order_by('article_count')
    elif sort_by_articles == 'desc':
        incidents = incidents.order_by('-article_count')
    elif sort_by_articles == 'date_asc':
        incidents = incidents.order_by('published')
    elif sort_by_articles == 'date_desc':
        incidents = incidents.order_by('-published')
    elif sort_by_articles == 'title_asc':
        incidents = incidents.order_by('title')
    elif sort_by_articles == 'title_desc':
        incidents = incidents.order_by('-title')

    context = {
        'incidents': incidents,
        'dimension_options': dimension_options,
        'phase_options': phase_options,
        'boundary_options': boundary_options,
        'recurring_options': recurring_options,
        'nature_options': nature_options,
        'intent_options': intent_options,
        'objective_options': objective_options,
        'capability_options': capability_options,
        'duration_options': duration_options,
        'behavior_options': behaviour_options,
        'dimension_options_selected': dimension_options_selected,
        'phase_options_selected': phase_options_selected,
        'boundary_options_selected': boundary_options_selected,
        'recurring_options_selected': recurring_options_selected,
        'nature_options_selected': nature_options_selected,
        'intent_options_selected': intent_options_selected,
        'objective_options_selected': objective_options_selected,
        'capability_options_selected': capability_options_selected,
        'duration_options_selected': duration_options_selected,
        'behavior_options_selected': behaviour_options_selected,
        'sort_by_articles': sort_by_articles
    }

    return render(request, 'articles/public_page.html', context)





# View for individual incident detail page
def incident_detail_view(request, pk):
    # Fetch the incident by primary key, or return 404 if not found
    incident = get_object_or_404(Incident, pk=pk)
    return render(request, 'articles/incident_detail.html', {'incident': incident})