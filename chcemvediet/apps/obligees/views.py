# vim: expandtab
import json, re
from unidecode import unidecode

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import model_to_dict
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Q

import models

def index(request):
    obligee_list = models.Obligee.objects.all()
    paginator = Paginator(obligee_list, 25)

    page = request.GET.get('page')
    try:
        obligee_page = paginator.page(page)
    except PageNotAnInteger:
        obligee_page = paginator.page(1)
    except EmptyPage:
        obligee_page = paginator.page(paginator.num_pages)

    context = {'obligee_page': obligee_page}
    return render(request, 'obligees/index.html', context)


def autocomplete(request):
    term = request.GET.get('term', '')
    term = unidecode(term).lower() # transliterate unicode to ascii
    words = filter(None, re.split(r'[^a-z0-9]+', term))

    query = reduce(lambda p, q: p & q, (Q(slug__contains='-'+w) for w in words), Q())
    obligee_list = models.Obligee.objects.filter(query).order_by('name')[:10]

    data = [{
        'label': obligee.name,
        'obligee': model_to_dict(obligee),
    } for obligee in obligee_list]

    return HttpResponse(json.dumps(data), content_type="application/json")

