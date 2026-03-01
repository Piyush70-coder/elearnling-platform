from django.contrib import admin
from django.db.models import Count, Sum, Avg
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models.functions import TruncMonth
from .models import Course, Enrollment, Lecture, LectureProgress, Quiz, Question, Answer, QuizAttempt, StudentAnswer, Review, Comment


class LectureInline(admin.TabularInline):
    model = Lecture
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'is_free', 'difficulty_level', 'enrollment_count', 'average_rating')
    list_filter = ('category', 'difficulty_level', 'is_free', 'is_active')
    search_fields = ('title', 'description', 'instructor__username')
    inlines = [LectureInline]
    
    def enrollment_count(self, obj):
        return obj.enrollments.count()
    enrollment_count.short_description = 'Enrollments'
    
    def average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        if avg:
            return f"{avg:.1f}/5.0"
        return "No ratings"
    average_rating.short_description = 'Rating'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('course_reports/', self.admin_site.admin_view(self.course_reports_view), name='course_reports'),
        ]
        return custom_urls + urls
    
    def course_reports_view(self, request):
        # Most popular courses by enrollment
        popular_courses = Course.objects.annotate(student_count=Count('enrollments')).order_by('-student_count')[:10]
        
        # Revenue by course
        revenue_by_course = Course.objects.filter(is_free=False).annotate(
            revenue=Count('enrollments') * Sum('price')
        ).order_by('-revenue')[:10]
        
        # Total students and revenue
        total_students = Enrollment.objects.count()
        total_revenue = sum(course.price * course.enrollments.count() for course in Course.objects.filter(is_free=False))
        
        context = {
            'title': 'Course Reports',
            'popular_courses': popular_courses,
            'revenue_by_course': revenue_by_course,
            'total_students': total_students,
            'total_revenue': total_revenue,
        }
        
        return TemplateResponse(request, 'admin/course_reports.html', context)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'time_limit_minutes', 'passing_score', 'attempts_allowed')
    list_filter = ('course', 'is_active')
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'quiz', 'question_type', 'points')
    list_filter = ('question_type', 'quiz')
    search_fields = ('question_text', 'quiz__title')
    inlines = [AnswerInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'rating', 'created_at', 'is_approved')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('student__username', 'course__title', 'comment')
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('student', 'lecture', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('student__username', 'lecture__title', 'content')
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"


# Register remaining models
admin.site.register(Enrollment)
admin.site.register(Lecture)
admin.site.register(LectureProgress)
admin.site.register(Answer)
admin.site.register(QuizAttempt)
admin.site.register(StudentAnswer)
