from .models import (
    Assignment,
    Building,
    Course,
    Department,
    ExternalCourse,
    Instructor,
    Meeting,
    Milestone,
    Reading,
    ReadingAssignment,
    Recitation,
    Submission,
    Unit,
    User,
    Viewing,
    ViewingAssignment,
    ViewingPart,
)
from django.contrib import admin
from django.forms import ModelForm, ChoiceField
from shared import bibutils


class ReadingForm(ModelForm):
    zotero_id = ChoiceField(choices=bibutils.load_zotero_library())

    class Meta:
        model = Reading
        fields = [
            "zotero_id",
            "description",
            "file",
            "url",
            "centiwords",
            "access_via_proxy",
            "ignore_citation_url",
        ]


class RecitationInline(admin.StackedInline):
    model = Recitation
    extra = 0


class MilestoneInline(admin.StackedInline):
    model = Milestone
    extra = 0


class ReadingAssignmentInline(admin.StackedInline):
    model = ReadingAssignment
    extra = 0


class ViewingAssignmentInline(admin.StackedInline):
    model = ViewingAssignment
    extra = 0


class ViewingPartInline(admin.StackedInline):
    model = ViewingPart
    extra = 3


class CourseAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_current")
    inlines = (RecitationInline, MilestoneInline)
    prepopulated_fields = {"slug": ("number",)}
    filter_horizontal = ("students",)
    ordering = ("is_archived",)
    save_as = True

    def is_current(self, course):
        return not course.is_archived

    is_current.boolean = True
    is_current.admin_order_field = "is_archived"

    def get_user_label(self, obj) -> str:
        return obj.get_full_name() or obj.username

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.remote_field.model == User:
            kwargs["queryset"] = User.objects.order_by("last_name", "username")
        field = super(CourseAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs
        )
        if db_field.remote_field.model == User:
            field.label_from_instance = self.get_user_label
        return field


class MeetingAdmin(admin.ModelAdmin):
    list_display = ("course", "__str__", "is_tentative")
    list_filter = ("course",)
    inlines = (ReadingAssignmentInline, ViewingAssignmentInline)
    save_as = True
    actions = ["make_tentative", "finalize"]

    def queryset(self, request):
        return (
            super(MeetingAdmin, self)
            .queryset(request)  # type: ignore
            .filter(course__is_archived=False)
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course":
            kwargs["queryset"] = Course.objects.filter(is_archived=False)
        return super(MeetingAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )

    def update_tentative(self, request, queryset, value):
        rows_updated = queryset.update(is_tentative=value)
        if rows_updated == 1:
            message = "1 meeting was"
        else:
            message = "%s meetings were" % rows_updated
        self.message_user(
            request,
            "%s successfully marked as %s."
            % (message, "tentative" if value else "finalized"),
        )

    def make_tentative(self, request, queryset):
        self.update_tentative(request, queryset, True)

    make_tentative.short_description = "Mark selected meetings as tentative"

    def finalize(self, request, queryset):
        self.update_tentative(request, queryset, False)

    finalize.short_description = "Mark selected meetings as finalized"


class UnitAdmin(admin.ModelAdmin):
    list_display = ("__str__", "course")
    save_as = True


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
    prepopulated_fields = {"slug": ("title",)}
    save_as = True
    ordering = ("-due_date",)


class ReadingAdmin(admin.ModelAdmin):
    form = ReadingForm
    readonly_fields = ("citation_text", "citation_html")


class ViewingAdmin(admin.ModelAdmin):
    inlines = (ViewingPartInline,)


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "submitter", "time_submitted", "get_grade")
    list_filter = ("assignment",)
    save_as = True

    def queryset(self, request):
        return (
            super(SubmissionAdmin, self)
            .queryset(request)  # type: ignore
            .filter(assignment__course__is_archived=False)
        )


admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Building)
admin.site.register(Course, CourseAdmin)
admin.site.register(ExternalCourse)
admin.site.register(Department)
admin.site.register(Instructor)
admin.site.register(Meeting, MeetingAdmin)
admin.site.register(Reading, ReadingAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Viewing, ViewingAdmin)
admin.site.register(ViewingPart)
