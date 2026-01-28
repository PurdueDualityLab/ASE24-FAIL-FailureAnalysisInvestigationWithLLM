import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from failures.articles.models import Incident
from django.db.models import Q

def check_incidents():
    print("Checking incidents for RAG eligibility...")
    
    # Logic from postmortemIncidentAutoVDB.py
    # incidents = Incident.objects.filter(Q(new_article=True) | Q(complete_report=False) | Q(complete_report=None))
    # incidents = incidents.exclude(experiment=True)
    
    # Check total incidents
    total_incidents = Incident.objects.count()
    print(f"Total incidents: {total_incidents}")
    
    # Check incidents matching the filter in the command
    pending_incidents = Incident.objects.filter(Q(new_article=True) | Q(complete_report=False) | Q(complete_report=None)).exclude(experiment=True).count()
    print(f"Incidents pending processing (new/incomplete): {pending_incidents}")

    # Check for incidents with enough tokens to trigger RAG (approx > 14k)
    # The command uses: if incident.tokens > prompt_window (approx 14885)
    # We'll just check if any have a high token count if calculated, or are generally large
    
    # Let's just list a few
    print("\nSample Incidents:")
    for incident in Incident.objects.all()[:5]:
        print(f"- ID: {incident.id}, Title: {incident.title}, Tokens: {incident.tokens}, New Article: {incident.new_article}")

if __name__ == "__main__":
    check_incidents()
