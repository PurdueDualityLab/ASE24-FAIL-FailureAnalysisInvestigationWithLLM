import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from failures.articles.models import Incident, Article, SearchQuery

def check_data():
    print("--- Data Status Check ---")
    
    sq_count = SearchQuery.objects.count()
    print(f"Search Queries: {sq_count}")
    
    article_count = Article.objects.count()
    print(f"Total Articles: {article_count}")
    
    articles_with_body = Article.objects.filter(body__isnull=False).exclude(body="").count()
    print(f"Articles with Body: {articles_with_body}")
    
    failures = Article.objects.filter(describes_failure=True).count()
    print(f"Articles classified as Failure: {failures}")
    
    analyzable = Article.objects.filter(analyzable_failure=True).count()
    print(f"Articles classified as Analyzable: {analyzable}")
    
    incident_count = Incident.objects.count()
    print(f"Total Incidents: {incident_count}")

    if article_count == 0:
        print("\n[Action Required] No articles found. You need to run 'scrape'.")
    elif failures == 0:
        print("\n[Action Required] Articles exist but none classified as failures. Run 'classifyfailure'.")
    elif incident_count == 0:
        print("\n[Action Required] Failures exist but no incidents. Run 'merge'.")
    else:
        print("\n[Status] Data seems present. If VectorDB is empty, run 'populatevectordb'.")

if __name__ == "__main__":
    check_data()
