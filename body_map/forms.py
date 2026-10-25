from django import forms

from body_map.models import Portrait, Subject


class ImportForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    photo = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': '.jpg,.jpeg,.png,.heic,.heif'})
    )
    chest = forms.ChoiceField(
        label='Chest', choices=Portrait.COVERAGE_CHOICES, widget=forms.RadioSelect
    )
    genitals = forms.ChoiceField(
        label='Sex', choices=Portrait.COVERAGE_CHOICES, widget=forms.RadioSelect
    )
    buttocks = forms.ChoiceField(
        label='Buttocks', choices=Portrait.COVERAGE_CHOICES, widget=forms.RadioSelect
    )

    @property
    def coverage_fields(self):
        return [self[area] for area in Portrait.COVERAGE_AREAS]

    def clean_subject(self):
        subject = self.cleaned_data['subject']
        if subject.portraits.filter(view='front').exists():
            raise forms.ValidationError('This subject already has a front portrait.')
        return subject
