from django.db import models
from django.conf import settings
from courses.models import Course, Enrollment
import uuid
from datetime import datetime

class Certificate(models.Model):
    """Model for storing certificate information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name='certificate')
    issue_date = models.DateTimeField(auto_now_add=True)
    certificate_file = models.FileField(upload_to='certificates/', blank=True, null=True)
    verification_link = models.URLField(blank=True, null=True)
    
    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"{self.user.username}'s certificate for {self.course.title}"
    
    def get_verification_url(self):
        """Returns the verification URL for this certificate"""
        if not self.verification_link:
            # Generate a verification link based on the certificate ID
            self.verification_link = f"/certificates/verify/{self.id}/"
            self.save()
        return self.verification_link
    
    @property
    def formatted_issue_date(self):
        """Returns a nicely formatted issue date"""
        return self.issue_date.strftime("%B %d, %Y")
