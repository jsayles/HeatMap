import shutil
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import redirect, render

from body_map.forms import ImportForm
from body_map.imaging import UnsupportedImage, clean_image
from body_map.models import Portrait, Subject, portrait_path


def home(request):
    subjects = Subject.objects.prefetch_related('portraits')
    return render(request, 'body_map/home.html', {'subjects': subjects})


def import_portrait(request):
    form = ImportForm(
        request.POST or None, request.FILES or None, initial={'subject': request.GET.get('subject')}
    )
    if request.method == 'POST' and form.is_valid():
        try:
            data, ext = clean_image(form.cleaned_data['photo'])
        except UnsupportedImage as error:
            form.add_error('photo', str(error))
        else:
            portrait = save_portrait(form.cleaned_data, data, ext)
            messages.success(request, f'Imported a portrait for {portrait.subject}.')
            return redirect('home')
    return render(request, 'body_map/import.html', {'form': form})


def save_portrait(cleaned, data, ext):
    portrait = None
    try:
        with transaction.atomic():
            portrait = Portrait.objects.create(
                subject=cleaned['subject'],
                chest=cleaned['chest'],
                genitals=cleaned['genitals'],
                buttocks=cleaned['buttocks'],
            )
            portrait.original.save(f'original.{ext}', ContentFile(data))
    except Exception:
        # Leave nothing behind if any step fails.
        if portrait is not None and portrait.pk:
            folder = Path(settings.MEDIA_ROOT, portrait_path(portrait, '')).parent
            shutil.rmtree(folder, ignore_errors=True)
        raise
    return portrait
