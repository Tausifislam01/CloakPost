from django.http import HttpResponse

def home(request):
    return HttpResponse("Cloakpost is alive.")
