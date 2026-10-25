import datetime

from django.core.exceptions import ValidationError
from django.db import models


class Subject(models.Model):
    """A person whose body is mapped. Separate from User, which is whoever logs in."""

    GENDER_CHOICES = (
        ('woman', 'Woman'),
        ('man', 'Man'),
        ('non_binary', 'Non-binary'),
        ('self_described', 'In my own words'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )

    display_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    gender = models.CharField(
        'Which best describes your gender?', max_length=20, choices=GENDER_CHOICES, blank=True
    )
    gender_self_description = models.CharField('In my own words', max_length=100, blank=True)
    pronouns = models.CharField(max_length=50, blank=True)
    year_of_birth = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('display_name',)

    def __str__(self):
        return self.display_name

    def clean(self):
        if self.gender == 'self_described':
            if not self.gender_self_description.strip():
                raise ValidationError(
                    {'gender_self_description': 'Describe your gender in your own words.'}
                )
        else:
            self.gender_self_description = ''

        if self.year_of_birth is not None:
            latest = datetime.date.today().year - 18
            if not 1900 <= self.year_of_birth <= latest:
                raise ValidationError(
                    {
                        'year_of_birth': f'Enter a year between 1900 and {latest}; subjects are adults.'
                    }
                )

    @property
    def file_id(self):
        # Files on disk identify a subject only by ID, never by name.
        return f'subject_{self.pk}'


def portrait_path(portrait, filename):
    return f'{portrait.subject.file_id}/portrait_{portrait.pk}/{filename}'


class Portrait(models.Model):
    VIEW_CHOICES = (('front', 'Front'),)
    COVERAGE_CHOICES = (
        ('exposed', 'Exposed'),
        ('covered', 'Covered'),
        ('not_in_photo', 'Not in photo'),
    )
    COVERAGE_AREAS = ('chest', 'genitals', 'buttocks')

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='portraits')
    view = models.CharField(max_length=20, choices=VIEW_CHOICES, default='front')
    imported_at = models.DateTimeField(auto_now_add=True)
    original = models.ImageField(upload_to=portrait_path, blank=True)

    # What the photo shows. "genitals" is labeled "Sex" in the app.
    chest = models.CharField(max_length=20, choices=COVERAGE_CHOICES)
    genitals = models.CharField('sex', max_length=20, choices=COVERAGE_CHOICES)
    buttocks = models.CharField(max_length=20, choices=COVERAGE_CHOICES)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('subject', 'view'), name='one_portrait_per_view'),
        )

    def __str__(self):
        return f'{self.subject} ({self.view})'

    @property
    def level(self):
        values = [getattr(self, area) for area in self.COVERAGE_AREAS]
        if 'exposed' not in values:
            return 'clothed'
        if 'covered' in values:
            return 'partly clothed'
        return 'nude'
