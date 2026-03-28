from django.http import HttpResponse
from django.urls import path
from django.views import View

from fetch_metadata.decorators import fetch_metadata_exempt, fetch_metadata_policy


def simple_view(request):
    return HttpResponse('ok')


@fetch_metadata_exempt
def exempt_view(request):
    return HttpResponse('ok')


@fetch_metadata_policy(allowed_sites=['same-origin', 'same-site', 'none'])
def custom_policy_view(request):
    return HttpResponse('ok')


@fetch_metadata_policy(allowed_sites=['same-origin'], allow_navigations=False, fail_open=False)
def strict_policy_view(request):
    return HttpResponse('ok')


@fetch_metadata_exempt
class ExemptCBV(View):
    def get(self, request):
        return HttpResponse('ok')

    def post(self, request):
        return HttpResponse('ok')


@fetch_metadata_policy(allowed_sites=['same-origin', 'cross-site'])
class CustomPolicyCBV(View):
    def post(self, request):
        return HttpResponse('ok')


def failure_view(request, reason=None, headers=None):
    return HttpResponse(f'custom 403: {reason}', status=403)


def broken_failure_view(request, reason=None, headers=None):
    raise ValueError('broken')


urlpatterns = [
    path('test/', simple_view, name='test'),
    path('exempt/', exempt_view, name='exempt'),
    path('custom-policy/', custom_policy_view, name='custom_policy'),
    path('strict-policy/', strict_policy_view, name='strict_policy'),
    path('cbv-exempt/', ExemptCBV.as_view(), name='cbv_exempt'),
    path('cbv-policy/', CustomPolicyCBV.as_view(), name='cbv_policy'),
]
