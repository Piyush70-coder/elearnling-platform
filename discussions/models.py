from django.db import models
from django.conf import settings
from courses.models import Course

class Discussion(models.Model):
    """
    Main discussion thread for a course
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='discussions_created'
    )
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return self.title

class Comment(models.Model):
    """
    Comments on discussion threads
    """
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_solution = models.BooleanField(default=False)  # Marked as solution by instructor
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.created_by.username} on {self.discussion.title}"

class Reaction(models.Model):
    """
    Reactions to discussions and comments (like, helpful, etc.)
    """
    REACTION_CHOICES = [
        ('like', 'Like'),
        ('helpful', 'Helpful'),
        ('insightful', 'Insightful'),
        ('confused', 'Confused'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('user', 'discussion', 'reaction_type'),
            ('user', 'comment', 'reaction_type'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(discussion__isnull=False) | models.Q(comment__isnull=False),
                name='reaction_has_target'
            ),
        ]
    
    def __str__(self):
        target = self.discussion or self.comment
        return f"{self.user.username} - {self.reaction_type} on {target}"
