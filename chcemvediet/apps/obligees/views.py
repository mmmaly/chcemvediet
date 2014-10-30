# vim: expandtab
# -*- coding: utf-8 -*-
import re
from unidecode import unidecode

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.forms.models import model_to_dict
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from poleno.utils.http import JsonResponse

from .models import Obligee

@require_http_methods([u'HEAD', u'GET'])
def index(request):
    obligee_list = Obligee.objects.pending()
    paginator = Paginator(obligee_list, 25)

    page = request.GET.get(u'page')
    try:
        obligee_page = paginator.page(page)
    except PageNotAnInteger:
        obligee_page = paginator.page(1)
    except EmptyPage:
        obligee_page = paginator.page(paginator.num_pages)

    ctx = {}
    ctx[u'obligee_page'] = obligee_page
    return render(request, u'obligees/index.html', ctx)

@require_http_methods([u'HEAD', u'GET'])
def autocomplete(request):
    term = request.GET.get(u'term', u'')
    term = unidecode(term).lower() # transliterate unicode to ascii
    words = (w for w in re.split(r'[^a-z0-9]+', term) if w)

    query = reduce(lambda p, q: p & q, (Q(slug__contains=u'-'+w) for w in words), Q())
    obligee_list = Obligee.objects.pending().filter(query)[:10]

    data = [{
        u'label': obligee.name,
        u'obligee': model_to_dict(obligee),
    } for obligee in obligee_list]

    return JsonResponse(data)

