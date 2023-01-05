from django.shortcuts import render

from .models import Failure


def index(request):
    return render(
        request,
        "articles/index.html",
        {
            "failures": Failure.objects.all(),
        },
    )
