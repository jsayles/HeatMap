from django.db import models


class Subject(models.Model):
    """A person whose body is mapped. Separate from User, which is whoever logs in."""

    display_name = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('display_name',)

    def __str__(self):
        return self.display_name

    @property
    def file_id(self):
        # Files on disk identify a subject only by ID, never by name.
        return f'subject_{self.pk}'
