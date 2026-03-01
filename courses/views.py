from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from django.db.models import Avg, Count
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.db import models
from accounts.models import AdminNotification
from .models import Course, Enrollment, Lecture, LectureProgress, Quiz, Question, Answer, QuizAttempt, StudentAnswer, Review, Comment
from .forms import CourseForm, LectureForm, QuizForm, QuestionForm, AnswerForm, QuestionFormSet, AnswerFormSet, ReviewForm, CommentForm
from accounts.decorators import is_teacher

# Course Views
def course_list(request):
    # Get all courses by default (both active and inactive)
    courses = Course.objects.all().order_by('-created_at')
    
    # Apply filters if provided
    category = request.GET.get('category')
    difficulty = request.GET.get('difficulty')  # Changed from level to difficulty
    language = request.GET.get('language')  # Added language filter
    search_query = request.GET.get('search')  # Added search query
    sort = request.GET.get('sort')
    
    if search_query:
        courses = courses.filter(
            models.Q(title__icontains=search_query) |
            models.Q(description__icontains=search_query) |
            models.Q(code__icontains=search_query)
        )
    
    if category:
        courses = courses.filter(category=category)
    
    if difficulty:  # Changed from level to difficulty
        courses = courses.filter(difficulty_level=difficulty)
    
    if language:  # Added language filter
        courses = courses.filter(programming_language=language)
    
    # Apply sorting
    if sort == 'popular':
        courses = courses.order_by('-enrollment_count')
    elif sort == 'rating':
        courses = courses.order_by('-avg_rating')
    else:  # newest (default)
        courses = courses.order_by('-created_at')
    
    # Get difficulty levels and programming languages for filter dropdowns
    difficulty_levels = dict(Course._meta.get_field('difficulty_level').choices)
    programming_languages = dict(Course._meta.get_field('programming_language').choices)
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(courses, 12)  # Show 12 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'difficulty_levels': difficulty_levels,
        'programming_languages': programming_languages,
        'search_query': search_query,
        'selected_difficulty': difficulty,
        'selected_language': language,
        'current_category': category,
        'current_sort': sort,
    }
    return render(request, 'courses/course_list.html', context)

@login_required
def create_course(request):
    if request.user.role != 'teacher':
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, f'Course "{course.title}" has been created successfully!')
            return redirect('courses:course_detail', course_id=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CourseForm()
    
    context = {
        'form': form
    }
    return render(request, 'courses/create_course.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lectures = Lecture.objects.filter(course=course).order_by('order')
    is_enrolled = False
    user_progress = None
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if is_enrolled:
            enrollment = Enrollment.objects.get(student=request.user, course=course)
            user_progress = enrollment.completion_percentage
    
    reviews = Review.objects.filter(course=course).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Check if current user is the instructor of this course
    is_instructor = request.user.is_authenticated and (request.user == course.instructor or request.user.is_staff)
    
    context = {
        'course': course,
        'lectures': lectures,
        'is_enrolled': is_enrolled,
        'user_progress': user_progress,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'is_instructor': is_instructor
    }
    return render(request, 'courses/course_detail.html', context)

@login_required
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course
    }
    return render(request, 'courses/edit_course.html', context)

@login_required
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    if request.method == 'POST':
        course.delete()
        return redirect('courses:course_list')
    
    context = {
        'course': course
    }
    return render(request, 'courses/delete_course.html', context)

@login_required
def enroll_course(request, course_id):
    if request.user.role != 'student':
        return redirect('courses:course_detail', course_id=course_id)
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('courses:course_detail', course_id=course_id)
    
    # Create enrollment
    enrollment = Enrollment(student=request.user, course=course)
    enrollment.save()
    
    return redirect('courses:course_detail', course_id=course_id)

@login_required
def unenroll_course(request, course_id):
    if request.user.role != 'student':
        return redirect('courses:course_detail', course_id=course_id)
    
    course = get_object_or_404(Course, id=course_id)
    
    # Check if enrolled
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.delete()
    except Enrollment.DoesNotExist:
        pass
    
    return redirect('courses:course_list')

@login_required
def manage_lectures(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    lectures = Lecture.objects.filter(course=course).order_by('order')
    
    context = {
        'course': course,
        'lectures': lectures
    }
    return render(request, 'courses/manage_lectures.html', context)

@login_required
def create_lecture(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = LectureForm(request.POST, request.FILES)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.course = course
            # Set order to be the next number
            last_order = Lecture.objects.filter(course=course).order_by('-order').first()
            lecture.order = last_order.order + 1 if last_order else 1
            lecture.save()
            messages.success(request, f'Lecture "{lecture.title}" has been created successfully!')
            return redirect('courses:manage_lectures', course_id=course.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LectureForm()
    
    context = {
        'form': form,
        'course': course
    }
    return render(request, 'courses/create_lecture.html', context)

@login_required
def view_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    
    # Check if user is enrolled or is the instructor
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not is_enrolled and request.user != course.instructor and not request.user.is_staff:
            return redirect('courses:course_detail', course_id=course.id)
    
    # Get all lectures for navigation
    all_lectures = Lecture.objects.filter(course=course).order_by('order')
    
    # Get lecture progress if user is a student
    lecture_progress = None
    if request.user.role == 'student' and is_enrolled:
        lecture_progress, created = LectureProgress.objects.get_or_create(
            student=request.user,
            lecture=lecture
        )
        
        # Update the last_lecture field in the enrollment
        enrollment = Enrollment.objects.get(student=request.user, course=course)
        enrollment.last_lecture = lecture
        enrollment.save(update_fields=['last_lecture'])
    
    # Get comments for this lecture
    comments = Comment.objects.filter(lecture=lecture).order_by('created_at')
    
    context = {
        'lecture': lecture,
        'course': course,
        'all_lectures': all_lectures,
        'lecture_progress': lecture_progress,
        'comments': comments,
        'comment_form': CommentForm()
    }
    return render(request, 'courses/lecture_detail.html', context)

@login_required
def edit_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:view_lecture', lecture_id=lecture.id)
    
    if request.method == 'POST':
        form = LectureForm(request.POST, request.FILES, instance=lecture)
        if form.is_valid():
            form.save()
            return redirect('courses:view_lecture', lecture_id=lecture.id)
    else:
        form = LectureForm(instance=lecture)
    
    context = {
        'form': form,
        'lecture': lecture,
        'course': course
    }
    return render(request, 'courses/edit_lecture.html', context)

@login_required
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    
    # Check if user is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:view_lecture', lecture_id=lecture.id)
    
    if request.method == 'POST':
        course_id = course.id
        lecture.delete()
        return redirect('courses:manage_lectures', course_id=course_id)
    
    context = {
        'lecture': lecture,
        'course': course
    }
    return render(request, 'courses/delete_lecture.html', context)

@login_required
@require_POST
def update_lecture_progress(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    
    # Check if user is enrolled
    if request.user.role != 'student':
        return redirect('courses:view_lecture', lecture_id=lecture.id)
    
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        return redirect('courses:course_detail', course_id=course.id)
    
    # Update or create lecture progress
    lecture_progress, created = LectureProgress.objects.get_or_create(
        student=request.user,
        lecture=lecture,
        defaults={'completed': True}
    )
    
    if not created:
        lecture_progress.completed = True
        lecture_progress.save()
    
    # Update enrollment completion percentage
    total_lectures = Lecture.objects.filter(course=course).count()
    completed_lectures = LectureProgress.objects.filter(
        student=request.user,
        lecture__course=course,
        completed=True
    ).count()
    
    if total_lectures > 0:
        completion_percentage = (completed_lectures / total_lectures) * 100
        enrollment.completion_percentage = completion_percentage
        enrollment.save()
    
    return redirect('courses:view_lecture', lecture_id=lecture.id)

# Quiz Views
@login_required
@is_teacher
@csrf_protect
def create_quiz(request, course_id):
    """Allow teachers to create a quiz for a specific course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if the teacher is the instructor of the course
    if request.user != course.instructor and not request.user.is_staff:
        messages.error(request, "You don't have permission to create quizzes for this course.")
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.course = course
            quiz.save()
            
            # Handle questions and answers using formsets
            question_formset = QuestionFormSet(request.POST, instance=quiz)
            if question_formset.is_valid():
                questions = question_formset.save(commit=False)
                
                # Process each question and its answers
                for question in questions:
                    question.quiz = quiz
                    question.save()
                    
                    # Handle answers for this question
                    answer_formset = AnswerFormSet(request.POST, instance=question, prefix=f'question_{question.id}')
                    if answer_formset.is_valid():
                        answers = answer_formset.save(commit=False)
                        for answer in answers:
                            answer.question = question
                            answer.save()
                
                messages.success(request, 'Quiz created successfully')
                return redirect('courses:quiz_list', course_id=course.id)
            else:
                messages.error(request, 'Error in question formset')
        else:
            messages.error(request, 'Error in quiz form')
    else:
        form = QuizForm()
        question_formset = QuestionFormSet()
    
    context = {
        'course': course,
        'form': form,
        'question_formset': question_formset,
    }
    return render(request, 'courses/create_quiz.html', context)

@login_required
def quiz_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled or is the instructor
    is_enrolled = False
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not is_enrolled and request.user != course.instructor and not request.user.is_staff:
            return redirect('courses:course_detail', course_id=course.id)
    
    # Only show active quizzes to students
    if request.user.role == 'student':
        quizzes = Quiz.objects.filter(course=course, is_active=True).order_by('created_at')
    else:
        # Teachers and staff can see all quizzes
        quizzes = Quiz.objects.filter(course=course).order_by('created_at')
    
    # Get quiz attempts for each quiz if user is a student
    quiz_data = []
    for quiz in quizzes:
        quiz_info = {
            'quiz': quiz,
            'attempts': [],
            'best_score': 0,
            'passed': False
        }
        
        if request.user.role == 'student' and is_enrolled:
            attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).order_by('-completed_at')
            quiz_info['attempts'] = attempts
            
            if attempts.exists():
                best_attempt = attempts.order_by('-score').first()
                quiz_info['best_score'] = best_attempt.score
                quiz_info['passed'] = best_attempt.score >= quiz.passing_score
        
        quiz_data.append(quiz_info)
    
    context = {
        'course': course,
        'quiz_data': quiz_data
    }
    return render(request, 'courses/quiz_list.html', context)

@login_required
def start_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is enrolled
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not is_enrolled:
            return redirect('courses:course_detail', course_id=course.id)
    elif request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    # Check if user has attempts left
    if quiz.max_attempts > 0 and request.user.role == 'student':
        attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz).count()
        if attempts >= quiz.max_attempts:
            return redirect('courses:quiz_list', course_id=course.id)
    
    # Create a new attempt
    attempt = QuizAttempt(student=request.user, quiz=quiz)
    attempt.save()
    
    return redirect('courses:take_quiz', quiz_id=quiz.id)

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course = quiz.course
    
    # Check if user is enrolled
    if request.user.role == 'student':
        is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not is_enrolled:
            return redirect('courses:course_detail', course_id=course.id)
    elif request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    # Get the latest attempt
    attempt = QuizAttempt.objects.filter(student=request.user, quiz=quiz, completed=False).order_by('-started_at').first()
    
    if not attempt:
        return redirect('courses:quiz_list', course_id=course.id)
    
    questions = Question.objects.filter(quiz=quiz).order_by('order')
    
    if request.method == 'POST':
        # Process quiz submission
        score = 0
        total_questions = questions.count()
        
        for question in questions:
            answer_key = f'question_{question.id}'
            student_answer_text = request.POST.get(answer_key, '')
            
            # Create student answer record
            student_answer = StudentAnswer(
                student=request.user,
                question=question,
                quiz_attempt=attempt,
                answer_text=student_answer_text
            )
            student_answer.save()
            
            # Check if answer is correct
            if question.question_type == 'multiple_choice':
                correct_answer = Answer.objects.filter(question=question, is_correct=True).first()
                if correct_answer and student_answer_text == str(correct_answer.id):
                    score += 1
                    student_answer.is_correct = True
                    student_answer.save()
            elif question.question_type == 'true_false':
                if (question.correct_answer.lower() == 'true' and student_answer_text.lower() == 'true') or \
                   (question.correct_answer.lower() == 'false' and student_answer_text.lower() == 'false'):
                    score += 1
                    student_answer.is_correct = True
                    student_answer.save()
            elif question.question_type in ['short_answer', 'coding']:
                # For short answer and coding, instructor will need to grade manually
                pass
        
        # Update attempt
        attempt.completed = True
        attempt.completed_at = timezone.now()
        attempt.score = (score / total_questions) * 100 if total_questions > 0 else 0
        attempt.save()
        
        return redirect('courses:quiz_results', quiz_id=quiz.id, attempt_id=attempt.id)
    
    # Prepare quiz questions with their answers
    quiz_questions = []
    for question in questions:
        answers = Answer.objects.filter(question=question)
        quiz_questions.append({
            'question': question,
            'answers': answers
        })
    
    context = {
        'quiz': quiz,
        'quiz_questions': quiz_questions,
        'attempt': attempt,
        'course': course
    }
    return render(request, 'courses/take_quiz.html', context)

@login_required
def quiz_results(request, quiz_id, attempt_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(QuizAttempt, id=attempt_id)
    course = quiz.course
    
    # Check if user is the student who took the quiz or the instructor
    if request.user != attempt.student and request.user != course.instructor and not request.user.is_staff:
        return redirect('courses:course_detail', course_id=course.id)
    
    # Get student answers
    student_answers = StudentAnswer.objects.filter(quiz_attempt=attempt).order_by('question__order')
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'course': course,
        'student_answers': student_answers,
        'passed': attempt.score >= quiz.passing_score
    }
    return render(request, 'courses/quiz_results.html', context)

# Review and Comment Views
@login_required
def add_review(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user is enrolled
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return redirect('courses:course_detail', course_id=course.id)
    
    # Check if user has already reviewed this course
    existing_review = Review.objects.filter(student=request.user, course=course).first()
    
    if request.method == 'POST':
        if existing_review:
            form = ReviewForm(request.POST, instance=existing_review)
        else:
            form = ReviewForm(request.POST)
        
        if form.is_valid():
            review = form.save(commit=False)
            if not existing_review:
                review.student = request.user
                review.course = course
            review.save()
            return redirect('courses:course_detail', course_id=course.id)
    else:
        if existing_review:
            form = ReviewForm(instance=existing_review)
        else:
            form = ReviewForm()
    
    context = {
        'form': form,
        'course': course,
        'is_update': existing_review is not None
    }
    return render(request, 'courses/add_review.html', context)

@login_required
@require_POST
def add_comment(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    course = lecture.course
    
    # Check if user is enrolled or is the instructor
    if request.user.role == 'student':
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return redirect('courses:course_detail', course_id=course.id)
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.student = request.user
        comment.lecture = lecture
        
        # Check if this is a reply to another comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
                comment.parent = parent_comment
            except Comment.DoesNotExist:
                pass
        
        comment.save()
    
    return redirect('courses:view_lecture', lecture_id=lecture.id)

# Dashboard Views
@login_required
def student_dashboard(request):
    # Ensure the user is authenticated and is a student
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('accounts:login')
    
    # Get all enrollments for the student
    enrollments = Enrollment.objects.filter(student=request.user)
    
    # Count completed courses (where completion_percentage is 100)
    completed_courses = enrollments.filter(completion_percentage=100).count()
    
    # Get recent quiz attempts
    recent_quiz_attempts = QuizAttempt.objects.filter(
        student=request.user
    ).order_by('-completed_at')[:5]
    
    # Count total quiz attempts
    quiz_attempts = QuizAttempt.objects.filter(student=request.user).count()
    
    context = {
        'enrollments': enrollments,
        'completed_courses': completed_courses,
        'recent_quiz_attempts': recent_quiz_attempts,
        'quiz_attempts': quiz_attempts,
    }
    
    return render(request, 'courses/student_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    # Ensure the user is authenticated and is an instructor
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('accounts:login')
    
    # Get all courses created by the instructor
    courses = Course.objects.filter(instructor=request.user)
    
    # Calculate total students enrolled in instructor's courses
    total_students = Enrollment.objects.filter(course__instructor=request.user).values('student').distinct().count()
    
    # Calculate total revenue from instructor's courses
    total_revenue = 0
    for course in courses:
        try:
            if not course.is_free and hasattr(course, 'price'):
                course_revenue = course.price * course.enrollments.count()
                course.revenue = course_revenue  # Add revenue as an attribute to each course
                total_revenue += course_revenue
        except Exception:
            # Handle case where price field might not exist
            course.revenue = 0
    
    # Get most popular courses by enrollment count
    popular_courses = courses.annotate(student_count=Count('enrollments')).order_by('-student_count')[:5]
    
    # Get courses by revenue
    revenue_courses = sorted([c for c in courses if hasattr(c, 'revenue') and c.revenue > 0], key=lambda x: x.revenue, reverse=True)[:5]
    
    context = {
        'courses': courses,
        'total_students': total_students,
        'total_revenue': total_revenue,
        'popular_courses': popular_courses,
        'revenue_courses': revenue_courses,
    }
    
    return render(request, 'courses/instructor_dashboard.html', context)


@login_required
def instructor_courses(request):
    # Ensure the user is authenticated and is an instructor
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('accounts:login')
    
    # Get all courses created by the instructor
    courses = Course.objects.filter(instructor=request.user).order_by('-created_at')
    
    # Calculate revenue for each course
    for course in courses:
        try:
            if not course.is_free and hasattr(course, 'price'):
                course.revenue = course.price * course.enrollments.count()
            else:
                course.revenue = 0
        except Exception:
            course.revenue = 0
    
    context = {
        'courses': courses,
        'title': 'My Courses'
    }
    
    return render(request, 'courses/instructor_courses.html', context)

@login_required
def student_courses(request):
    # Ensure the user is authenticated and is a student
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('accounts:login')
    
    # Get all courses the student is enrolled in
    enrollments = Enrollment.objects.filter(student=request.user, is_active=True).order_by('-enrolled_at')
    
    context = {
        'enrollments': enrollments,
        'title': 'My Enrolled Courses'
    }
    
    return render(request, 'courses/enrolled_courses.html', context)
