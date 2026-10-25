from django.contrib import messages
from django.shortcuts import redirect, render

from body_map.forms import ImportForm
from body_map.imaging import UnsupportedImage
from body_map.models import Portrait, Subject
from body_map.outline import NoUsableOutline
from body_map.pipeline import import_portrait as run_import


def home(request):
    subjects = Subject.objects.prefetch_related('portraits')
    return render(request, 'body_map/home.html', {'subjects': subjects})


def import_portrait(request):
    form = ImportForm(
        request.POST or None, request.FILES or None, initial={'subject': request.GET.get('subject')}
    )
    if request.method == 'POST' and form.is_valid():
        coverage = {area: form.cleaned_data[area] for area in Portrait.COVERAGE_AREAS}
        try:
            portrait = run_import(
                form.cleaned_data['subject'], form.cleaned_data['photo'], coverage
            )
        except (UnsupportedImage, NoUsableOutline) as error:
            form.add_error('photo', str(error))
        else:
            messages.success(request, f'Imported a portrait for {portrait.subject}.')
            return redirect('home')
    return render(request, 'body_map/import.html', {'form': form})
