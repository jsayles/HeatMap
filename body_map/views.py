from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from body_map import svg
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
            return redirect('portrait_detail', pk=portrait.pk)
    return render(request, 'body_map/import.html', {'form': form})


def portrait_detail(request, pk):
    portrait = get_object_or_404(Portrait.objects.select_related('subject'), pk=pk)
    keypoints = list(portrait.keypoints.all())
    grid_width, grid_height = settings.GRID_SIZE
    nose_x, nose_y = settings.GRID_NOSE_BRIDGE
    half_shoulders = settings.GRID_SHOULDER_WIDTH / 2
    context = {
        'portrait': portrait,
        'coverage': [
            (Portrait._meta.get_field(area).verbose_name.capitalize(), portrait.get_coverage(area))
            for area in Portrait.COVERAGE_AREAS
        ],
        'outline_px': svg.path_data(portrait.outline_px),
        'points_px': svg.keypoint_marks(keypoints),
        'outline_grid': svg.path_data(portrait.outline_grid),
        'grid': {
            'width': grid_width,
            'height': grid_height,
            'nose_x': nose_x,
            'nose_y': nose_y,
            'shoulder_left': nose_x - half_shoulders,
            'shoulder_right': nose_x + half_shoulders,
        },
    }
    return render(request, 'body_map/portrait_detail.html', context)


def overlay(request):
    portraits = Portrait.objects.filter(alignment_status='aligned').exclude(outline_grid=None)
    grid_width, grid_height = settings.GRID_SIZE
    nose_x, nose_y = settings.GRID_NOSE_BRIDGE
    context = {
        'outlines': [svg.path_data(p.outline_grid) for p in portraits],
        'grid': {'width': grid_width, 'height': grid_height, 'nose_x': nose_x, 'nose_y': nose_y},
    }
    return render(request, 'body_map/overlay.html', context)
