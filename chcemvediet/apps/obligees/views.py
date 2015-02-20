# vim: expandtab
# -*- coding: utf-8 -*-
import re
import operator
from unidecode import unidecode

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.forms.models import model_to_dict
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.http import JsonResponse

from .models import Obligee

@require_http_methods([u'HEAD', u'GET'])
def index(request):
    obligees = Obligee.objects.pending()
    paginator = Paginator(obligees, 25)

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

    query = reduce(operator.and_, (Q(slug__contains=u'-'+w) for w in words), Q())
    obligees = Obligee.objects.pending().filter(query)[:10]

    data = [{
        u'label': obligee.name,
        u'obligee': model_to_dict(obligee),
    } for obligee in obligees]

    # Note: Jquery-ui autocomplete expects JSON with Array, despite possible problems with
    # poisoning the JavaScript Array constructor.
    # See: https://docs.djangoproject.com/en/1.8/ref/request-response/#serializing-non-dictionary-objects
    return JsonResponse(data, safe=False)
