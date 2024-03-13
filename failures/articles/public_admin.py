from public_admin.admin import PublicModelAdmin
from public_admin.sites import PublicAdminSite, PublicApp

from failures.articles.models import Article, Incident
from failures.articles.admin import ArticleAdmin, IncidentAdmin

public_app = PublicApp("articles", models=("Article", "Incident"))
public_admin = PublicAdminSite("dashboard", public_app)
public_admin.register(Article, ArticleAdmin)
public_admin.register(Incident, IncidentAdmin)