from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def page(request, template_name):
    return render(request, template_name)


@ensure_csrf_cookie
def csrf_cookie(request):
    return JsonResponse({"ok": True})
