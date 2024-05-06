from django import forms

from .models import Comment, Resource
import magic
from django.utils import timezone

MAX_UPLOAD_SIZE = 1024*1024*2
ACCEPTABLE_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif']

class ResetMixin:
    @staticmethod
    def last_reset_was_24_hours_ago(last_reset):
        today_minus_24 = timezone.now() - timezone.timedelta(days=1)
        return last_reset < today_minus_24


class BaseUserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)

    def validate_quota(self, quota_field):
        user = self.request.user
        remaining_quota = getattr(user, quota_field)

        error_field =  self.Meta.quota_mappings.get(quota_field)
        error_msg = self.Meta.quota_error_msg.get(quota_field)

        if remaining_quota > 0:
            setattr(user, quota_field, remaining_quota - 1)
            user.save()
        elif ResetMixin.last_reset_was_24_hours_ago(user.last_reset):
            user.reset_form_quota()
            remaining_quota = getattr(user, quota_field)
            setattr(user, quota_field, remaining_quota - 1)
            user.save()
        else:
            self.add_error(error_field, error_msg)
    """
    Form for the Comment model related to:
    models:
        :model:`library.Material`.
    view:
        :view:`library.views.CommentFormView`.
    """
    class Meta:
        model = Comment
        fields = ['comment']
        labels = {
            'comment': 'Comentario',  
        }
        widgets = {
            'comment':
            forms.Textarea(attrs={
                'class': 'texto-formulario cuadros',
            }),
        }


class MaterialUploadForm(forms.ModelForm):
    """
    Form for the Comment model related to:
    models:
        :model:`library.Material`.
    view:
        :view:`library.views.CommentFormView`.
    """

    class Meta:
        model = Resource
        fields = '__all__'
        
    def clean_upload(self):
        """
        Validates the uploaded file. 
        The file should not exceed 2MB and should be either a PDF or an image (JPEG, PNG, or GIF).
        """
        cleaned_data = super().clean()
        upload = cleaned_data.get('upload')
    
        if upload:
            myFile = upload.open()
            mime = magic.from_buffer(myFile.read(2048), mime=True)

            if upload.size > MAX_UPLOAD_SIZE:
                self.add_error('upload', 'El archivo es demasiado grande')
            elif mime not in ACCEPTABLE_MIME_TYPES:
                self.add_error('upload', 'El archivo no es un PDF o una imagen')

        return upload

    
