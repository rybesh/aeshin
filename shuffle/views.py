from django.shortcuts import render
import random

concepts = [
    'Clint Eastwood',
    'homesick',
    'loud',
    'microwave',
    'poverty',
    'television',
]


def index(request):
    return render(
        request,
        'results.html',
        context={'items': random.sample(concepts, k=len(concepts))}
    )
