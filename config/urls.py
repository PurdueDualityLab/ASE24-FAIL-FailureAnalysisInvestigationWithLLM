from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse, JsonResponse
from django.urls import include, path
from django.views import defaults as default_views

from failures.articles.public_admin import public_admin


def landing_page(request):
    return HttpResponse(
        """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Software Failures</title>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f7fb; color: #1f2937; }
    .wrap { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
    .card { max-width: 760px; width: 100%; background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 28px; box-shadow: 0 10px 30px rgba(0,0,0,.05); }
    h1 { margin: 0 0 10px; font-size: 34px; }
    p { margin: 0 0 20px; line-height: 1.5; color: #4b5563; }
    .row { display: flex; gap: 12px; flex-wrap: wrap; }
    a.btn { text-decoration: none; border-radius: 10px; padding: 12px 16px; font-weight: 600; }
    .primary { background: #111827; color: #fff; }
    .secondary { background: #e5e7eb; color: #111827; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Software Failures</h1>
      <p>Browse the failure database or use FailBot for interactive analysis.</p>
      <div class="row">
        <a class="btn primary" href="/database/">Open Database</a>
        <a class="btn secondary" href="/failbot/">Open FailBot</a>
      </div>
    </div>
  </div>
</body>
</html>
""",
        content_type="text/html",
    )


urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    path('health/', lambda request: JsonResponse({"status": "healthy"}, status=200), name='health_check'),
    path("", landing_page, name="landing_page"),
    path("database/", include("failures.articles.urls", namespace="articles")),
    # path("", public_admin.urls),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
