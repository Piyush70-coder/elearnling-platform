from django import forms
from .models import Assignment, AssignmentUpload

class AssignmentForm(forms.ModelForm):
    assignment_file = forms.FileField(required=False, help_text="Upload a PDF file for this assignment")
    
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'due_date', 'programming_language', 'difficulty', 'max_score']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class AssignmentUploadForm(forms.ModelForm):
    class Meta:
        model = AssignmentUpload
        fields = ['file', 'title', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }