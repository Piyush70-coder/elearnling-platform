from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q
from .models import Discussion, Comment, Reaction
from courses.models import Course
from .forms import DiscussionForm, CommentForm

@login_required
def discussion_list(request, course_id):
    """
    List all discussions for a specific course
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled in the course or is the instructor
    if not (request.user == course.instructor or 
            course.enrollments.filter(student=request.user, is_active=True).exists()):
        messages.error(request, "You must be enrolled in this course to view discussions.")
        return redirect('courses:detail', course_id=course_id)
    
    # Get discussions with comment counts
    discussions = Discussion.objects.filter(course=course)\
        .annotate(comment_count=Count('comments'))\
        .order_by('-is_pinned', '-created_at')
    
    context = {
        'course': course,
        'discussions': discussions,
    }
    return render(request, 'discussions/discussion_list.html', context)

@login_required
def discussion_detail(request, discussion_id):
    """
    View a specific discussion and its comments
    """
    discussion = get_object_or_404(Discussion, id=discussion_id)
    course = discussion.course
    
    # Check if user is enrolled in the course or is the instructor
    if not (request.user == course.instructor or 
            course.enrollments.filter(student=request.user, is_active=True).exists()):
        messages.error(request, "You must be enrolled in this course to view discussions.")
        return redirect('courses:detail', course_id=course.id)
    
    # Get all top-level comments
    comments = Comment.objects.filter(discussion=discussion, parent=None).order_by('created_at')
    
    # Get top 5 popular comments based on reaction count
    # Annotate comments with total reaction count and order by count
    top_comments = Comment.objects.filter(discussion=discussion)\
        .annotate(total_reactions=Count('reactions'))\
        .order_by('-total_reactions', '-created_at')[:5]
    
    # Handle new comment submission
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.discussion = discussion
            comment.created_by = request.user
            
            # Check if this is a reply to another comment
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = get_object_or_404(Comment, id=parent_id)
            
            comment.save()
            messages.success(request, "Your comment has been posted.")
            return redirect('discussions:detail', discussion_id=discussion_id)
    else:
        form = CommentForm()
    
    context = {
        'discussion': discussion,
        'comments': comments,
        'top_comments': top_comments,
        'form': form,
    }
    return render(request, 'discussions/discussion_detail.html', context)

@login_required
def create_discussion(request, course_id):
    """
    Create a new discussion thread
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled in the course or is the instructor
    if not (request.user == course.instructor or 
            course.enrollments.filter(student=request.user, is_active=True).exists()):
        messages.error(request, "You must be enrolled in this course to create discussions.")
        return redirect('courses:detail', course_id=course_id)
    
    if request.method == 'POST':
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.course = course
            discussion.created_by = request.user
            discussion.save()
            messages.success(request, "Discussion created successfully.")
            return redirect('discussions:detail', discussion_id=discussion.id)
    else:
        form = DiscussionForm()
    
    context = {
        'course': course,
        'form': form,
    }
    return render(request, 'discussions/create_discussion.html', context)

@login_required
def toggle_reaction(request):
    """
    Add or remove a reaction to a discussion or comment
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    reaction_type = request.POST.get('reaction_type')
    discussion_id = request.POST.get('discussion_id')
    comment_id = request.POST.get('comment_id')
    
    if not reaction_type or (not discussion_id and not comment_id):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)
    
    # Determine the target (discussion or comment)
    target = None
    if discussion_id:
        target = get_object_or_404(Discussion, id=discussion_id)
        # Check if user can access this discussion
        if not (request.user == target.course.instructor or 
                target.course.enrollments.filter(student=request.user, is_active=True).exists()):
            return JsonResponse({'error': 'Access denied'}, status=403)
    elif comment_id:
        target = get_object_or_404(Comment, id=comment_id)
        # Check if user can access this comment's discussion
        if not (request.user == target.discussion.course.instructor or 
                target.discussion.course.enrollments.filter(student=request.user, is_active=True).exists()):
            return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Check if reaction already exists
    if discussion_id:
        existing_reaction = Reaction.objects.filter(
            user=request.user,
            discussion_id=discussion_id,
            reaction_type=reaction_type
        ).first()
    else:
        existing_reaction = Reaction.objects.filter(
            user=request.user,
            comment_id=comment_id,
            reaction_type=reaction_type
        ).first()
    
    # Toggle reaction (remove if exists, add if doesn't)
    if existing_reaction:
        existing_reaction.delete()
        action = 'removed'
    else:
        reaction = Reaction(
            user=request.user,
            reaction_type=reaction_type
        )
        if discussion_id:
            reaction.discussion_id = discussion_id
        else:
            reaction.comment_id = comment_id
        reaction.save()
        action = 'added'
    
    # Get updated reaction counts
    if discussion_id:
        reaction_counts = Reaction.objects.filter(discussion_id=discussion_id)\
            .values('reaction_type').annotate(count=Count('id'))
    else:
        reaction_counts = Reaction.objects.filter(comment_id=comment_id)\
            .values('reaction_type').annotate(count=Count('id'))
    
    # Format counts for response
    counts = {item['reaction_type']: item['count'] for item in reaction_counts}
    
    return JsonResponse({
        'success': True,
        'action': action,
        'reaction_counts': counts
    })

@login_required
def mark_as_solution(request, comment_id):
    """
    Mark a comment as the solution to a discussion
    Only course instructors can mark solutions
    """
    comment = get_object_or_404(Comment, id=comment_id)
    discussion = comment.discussion
    course = discussion.course
    
    # Only instructors can mark solutions
    if request.user != course.instructor:
        messages.error(request, "Only instructors can mark solutions.")
        return redirect('discussions:detail', discussion_id=discussion.id)
    
    # Toggle solution status
    comment.is_solution = not comment.is_solution
    comment.save()
    
    if comment.is_solution:
        messages.success(request, "Comment marked as solution.")
    else:
        messages.success(request, "Solution mark removed.")
    
    return redirect('discussions:detail', discussion_id=discussion.id)

@login_required
def update_comment(request, comment_id):
    """
    Update an existing comment
    Only the comment creator can update their comment
    """
    comment = get_object_or_404(Comment, id=comment_id)
    discussion = comment.discussion
    
    # Check if user is the comment creator
    if request.user != comment.created_by:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'You can only edit your own comments.'}, status=403)
        messages.error(request, "You can only edit your own comments.")
        return redirect('discussions:detail', discussion_id=discussion.id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            
            # For AJAX requests, return JSON response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'content': comment.content
                })
                
            messages.success(request, "Comment updated successfully.")
            return redirect('discussions:detail', discussion_id=discussion.id)
        else:
            # For AJAX requests, return errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Invalid form data.'}, status=400)
    else:
        form = CommentForm(instance=comment)
    
    context = {
        'form': form,
        'comment': comment,
        'discussion': discussion
    }
    return render(request, 'discussions/edit_comment.html', context)
