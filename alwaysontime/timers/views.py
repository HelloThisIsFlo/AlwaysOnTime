from allauth.socialaccount.models import SocialToken
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def index(request):
    access_token = SocialToken.objects.get(account__user=request.user)

    return render(request, 'index.html', {
        'token': access_token
    })
