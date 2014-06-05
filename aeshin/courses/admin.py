from models import *
from django.contrib import admin
from django.forms import ModelForm, ChoiceField
from shared import bibutils

class ReadingForm(ModelForm):
    zotero_id = ChoiceField(choices=bibutils.load_zotero_library())
    class Meta:
        model = Reading

class HolidayInline(admin.StackedInline):
    model = Holiday
    extra = 0

class ReadingAssignmentInline(admin.StackedInline):
    model = ReadingAssignment
    extra = 0

class CourseAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'is_current')
    inlines = (HolidayInline,)
    prepopulated_fields = { 'slug': ('number',) }
    filter_horizontal = ('students',)
    ordering = ('is_archived',)
    save_as = True
    def is_current(self, course):
        return not course.is_archived
    is_current.boolean = True
    is_current.admin_order_field = 'is_archived'
    def get_user_label(self, user):
        return (user.get_full_name() or user.username)
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.rel.to == User:
            kwargs['queryset'] = User.objects.order_by('last_name', 'username')
        field = super(CourseAdmin, self)\
            .formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.rel.to == User:
            field.label_from_instance = self.get_user_label
        return field

class MeetingAdmin(admin.ModelAdmin):
    list_display = ('course', '__unicode__', 'is_tentative')
    inlines = (ReadingAssignmentInline,)
    save_as = True
    actions = [ 'make_tentative', 'finalize' ]
    def queryset(self, request):
        return super(MeetingAdmin, self).queryset(request)\
            .filter(course__is_archived=False)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'course':
            kwargs['queryset'] = Course.objects.filter(is_archived=False)
        return super(MeetingAdmin, self)\
            .formfield_for_foreignkey(db_field, request, **kwargs)
    def update_tentative(self, request, queryset, value):
        rows_updated = queryset.update(is_tentative=value)
        if rows_updated == 1:
            message = '1 meeting was'
        else:
            message = '%s meetings were' % rows_updated
        self.message_user(request, '%s successfully marked as %s.' 
                          % (message, 'tentative' if value else 'finalized'))
    def make_tentative(self, request, queryset):
        self.update_tentative(request, queryset, True)
    make_tentative.short_description = 'Mark selected meetings as tentative'
    def finalize(self, request, queryset):
        self.update_tentative(request, queryset, False)
    finalize.short_description = 'Mark selected meetings as finalized'

class AssignmentAdmin(admin.ModelAdmin):
    prepopulated_fields = { 'slug': ('title',) }
    save_as = True
    ordering = ('-due_date',)

class ReadingAdmin(admin.ModelAdmin):
    form = ReadingForm
    readonly_fields = ('citation_text', 'citation_html')

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'submitter', 'time_submitted', 'get_grade')
    list_filter = ('assignment',)
    save_as = True
    def queryset(self, request):
        return super(SubmissionAdmin, self).queryset(request)\
            .filter(assignment__course__is_archived=False)

admin.site.register(Course, CourseAdmin)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Reading, ReadingAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Instructor)
