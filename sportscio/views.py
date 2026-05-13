# AI Prompt: "How do I limit view compatibility based on user identity through authentication?"
# Notes: Handles complex logic for rendering a monthly calendar grid and implements restrictions to redirect 'user_admin' roles to their specific dashboard.

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import connection
from django.shortcuts import get_object_or_404
from datetime import date, datetime, time, timedelta
import calendar as pycal
import json
from .models import ClubDocument, Message, Announcement, Event, Profile
from .permissions import is_officer, is_user_admin, is_privileged

#Django views, handles CRUD operations for events, announcements, documents, and user role management, calendar rendering

def _parse_dt_local(value: str):
    """
    Parse <input type="datetime-local"> value into an aware datetime in the current TIME_ZONE.
    """
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt)
    return dt


def _validate_event_not_in_past(start_dt, end_dt):
    """Return an error string if start/end are not strictly in the future, else None."""
    now = timezone.now()
    if start_dt < now:
        return "Start time cannot be in the past."
    if end_dt < now:
        return "End time cannot be in the past."
    return None


class CalendarEventChip:
    """One calendar cell row: real Event bounds plus times clipped to that local calendar day."""

    __slots__ = (
        "id",
        "title",
        "description",
        "location",
        "event_type",
        "start_time",
        "end_time",
        "segment_start",
        "segment_end",
    )

    def __init__(
        self,
        event: Event,
        segment_start,
        segment_end,
    ):
        self.id = event.id
        self.title = event.title
        self.description = event.description
        self.location = event.location
        self.event_type = event.event_type
        self.start_time = event.start_time
        self.end_time = event.end_time
        self.segment_start = segment_start
        self.segment_end = segment_end


def _calendar_chip_for_day(event: Event, day: date):
    """Clip event to local [day 00:00, day 23:59:59.999999] for display on that grid cell."""
    day_start = timezone.make_aware(datetime.combine(day, time.min))
    day_end = timezone.make_aware(datetime.combine(day, time.max))
    seg_start = max(event.start_time, day_start)
    seg_end = min(event.end_time, day_end)
    return CalendarEventChip(event, seg_start, seg_end)

# View functions below, decorated with @login_required and role checks to enforce access control based on user identity and permissions.
@login_required
def home(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    return redirect("dashboard")


@login_required
def whoami_view(request):
    try:
        profile = request.user.profile
        role = profile.role
    except Profile.DoesNotExist:
        role = None
    db = connection.settings_dict
    # user and database info for debugging purposes, but only for authenticated users since this is protected by @login_required
    return JsonResponse(
        {
            "user_id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "is_authenticated": request.user.is_authenticated,
            "role": role,
            "is_user_admin": is_user_admin(request.user),
            "is_officer": is_officer(request.user),
            "is_superuser": request.user.is_superuser,
            "db_name": db.get("NAME"),
            "db_host": db.get("HOST"),
        }
    )


@login_required
def dashboard_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin") # redirect user_admins to their specific dashboard instead of general one

    announcements = Announcement.objects.filter(is_active=True).order_by("-created_at")[:3]
    now = timezone.now()
    events = (
        Event.objects.filter(start_time__gte=now).order_by("start_time")[:3]
    )

    return render(
        request,
        "dashboard.html",
        {
            "announcements": announcements,
            "events": events,
            "nav_active": "dashboard",
        },
    )


@login_required
def calendar_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    #Get timezone conscious local month range with sanity checks
    today = timezone.localdate()
    try:
        y = int(request.GET.get("year", today.year))
        m = int(request.GET.get("month", today.month))
    except (ValueError, TypeError):
        y, m = today.year, today.month
    if m < 1 or m > 12:
        y, m = today.year, today.month
    if y < 1970 or y > 2100:
        y = today.year

    first_day = date(y, m, 1)
    last_n = pycal.monthrange(y, m)[1]
    last_day = date(y, m, last_n)

    start_dt = timezone.make_aware(datetime.combine(first_day, time.min))
    end_dt = timezone.make_aware(datetime.combine(last_day, time.max))

    events_qs = Event.objects.filter(
        start_time__lte=end_dt,
        end_time__gte=start_dt,
    ).order_by("start_time")
#build mapping of date, list of event segments for that date
    by_day = {}
    for e in events_qs:
        #convert into times into local dates
        sd = timezone.localtime(e.start_time).date()
        ed = timezone.localtime(e.end_time).date()
        #clip to calendar month range
        d = max(sd, first_day)
        end = min(ed, last_day)
        #iterate from d to end, adding event chip for that day
        while d <= end:
            by_day.setdefault(d.isoformat(), []).append(_calendar_chip_for_day(e, d))
            d += timedelta(days=1)

    for key, lst in by_day.items():
        lst.sort(key=lambda chip: (chip.segment_start, chip.start_time))

    cal = pycal.Calendar(firstweekday=pycal.SUNDAY)
    weeks = cal.monthdatescalendar(y, m)

    calendar_weeks = []
    for week in weeks:
        row = []
        for d in week:
            key = d.isoformat()
            row.append(
                {
                    "date": d,
                    "in_month": d.month == m and d.year == y,
                    "is_today": d == today,
                    "events": by_day.get(key, []),
                }
            )
        calendar_weeks.append(row)

    if m == 1:
        prev_y, prev_m = y - 1, 12
    else:
        prev_y, prev_m = y, m - 1
    if m == 12:
        next_y, next_m = y + 1, 1
    else:
        next_y, next_m = y, m + 1

    month_label = date(y, m, 1).strftime("%B %Y")

    return render(
        request,
        "calendar.html",
        {
            "nav_active": "calendar",
            "calendar_weeks": calendar_weeks,
            "month_label": month_label,
            "cal_year": y,
            "cal_month": m,
            "prev_y": prev_y,
            "prev_m": prev_m,
            "next_y": next_y,
            "next_m": next_m,
            "today": today,
        },
    )


@login_required
def members_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "members.html", {"users": users, "nav_active": "members"})


@login_required
def documents_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")

    docs = ClubDocument.objects.select_related("uploaded_by")
    # only show documents uploaded by officers or execs to regular members, but show all to officers and execs
    if request.method == "POST":
        if not is_privileged(request.user):
            django_messages.error(request, "Only club leaders can upload documents.")
            return redirect("documents")
        title = request.POST.get("title", "").strip()
        upload = request.FILES.get("file")
        if not title or not upload:
            django_messages.error(request, "Title and file are required.")
            return redirect("documents")
        max_bytes = 15 * 1024 * 1024 # 15MB limit
        if upload.size > max_bytes:
            django_messages.error(request, "File must be 15MB or smaller.")
            return redirect("documents")
        ClubDocument.objects.create(
            uploaded_by=request.user,
            title=title[:200],
            file=upload,
        )
        django_messages.success(request, "Document uploaded.")
        return redirect("documents")

    return render(
        request,
        "documents.html",
        {"nav_active": "documents", "documents": docs},
    )


@login_required
def profile_settings_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")

    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    # Only allow user_admins to access their role management dashboard, not profile settings,
    # to avoid confusion since they can't use other app features. All other roles can access profile settings.
    if request.method == "POST":
        first = request.POST.get("first_name", "").strip()
        last = request.POST.get("last_name", "").strip()
        birthday_raw = request.POST.get("birthday", "").strip()
        
        email_notifs = request.POST.get("email_notifications") == "on"

        user.first_name = first[:150]
        user.last_name = last[:150]
        user.save(update_fields=["first_name", "last_name"])

        profile.email_notifications = email_notifs

        if birthday_raw: # optional field, can be blank to clear
            try:
                profile.birthday = datetime.strptime(birthday_raw, "%Y-%m-%d").date()
            except ValueError:
                django_messages.error(request, "Please use a valid birthday date.")
                return redirect("profile_settings")
        else:
            profile.birthday = None

        if "avatar" in request.FILES: # optional field, only update if provided
            img = request.FILES["avatar"]
            if img.size > 2 * 1024 * 1024: # 2MB limit for profile photos
                django_messages.error(request, "Profile photo must be 2MB or smaller.")
                return redirect("profile_settings")
            profile.avatar = img

        profile.save()
        django_messages.success(request, "Your profile was updated.")
        return redirect("profile_settings")

    return render(request, "profile_settings.html", {"nav_active": "profile"})


@login_required
def cio_profile_view(request):
    return redirect("dashboard")


@login_required
def user_profile_view(request):
    return redirect("dashboard")


@login_required
@user_passes_test(is_officer)
def exec_profile_view(request):
    return redirect("dashboard")


@login_required
def messages_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    # only show general room messages to regular members, but show all to officers and execs, and redirect user_admins to their dashboard
    msgs = (
        Message.objects.filter(room="general").order_by("-timestamp")[:50][::-1]
    )
    return render(
        request,
        "messages.html",
        {"chat_messages": msgs, "nav_active": "messages", "chat_room": "general"},
    )


@login_required
@user_passes_test(is_privileged)
def messages_admin_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    
    # only show general room messages to regular members, but show all to officers and execs, and redirect user_admins to their dashboard
    msgs = Message.objects.filter(room="admin").order_by("-timestamp")[:50][::-1]
    return render(
        request,
        "messages_admin.html",
        {"chat_messages": msgs, "nav_active": "messages_admin", "chat_room": "admin"},
    )


@login_required
@user_passes_test(is_privileged)
def new_event_view(request):
    error = None
    # displays fields for creating a new event, and handles validation and saving of that event, with access restricted to officers and execs
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        start_time_raw = request.POST.get("start_time", "").strip()
        end_time_raw = request.POST.get("end_time", "").strip()
        location = request.POST.get("location", "").strip()
        event_type = request.POST.get("event_type", "").strip()
        description = request.POST.get("description", "").strip()

        start_dt = _parse_dt_local(start_time_raw)
        end_dt = _parse_dt_local(end_time_raw)

        if not title or not start_dt or not end_dt:
            error = "Title, start time, and end time are required."
        elif end_dt <= start_dt:
            error = "End time must be after start time."
        else:
            error = _validate_event_not_in_past(start_dt, end_dt)
            if error is None:
                Event.objects.create(
                    created_by=request.user,
                    title=title,
                    start_time=start_dt,
                    end_time=end_dt,
                    location=location[:200],
                    event_type=event_type[:32],
                    description=description,
                )
                return redirect("calendar")
    return render(
        request,
        "new_event.html",
        {"error": error, "nav_active": "calendar"},
    )


@login_required
def admin_profile_view(request):
    if not request.user.is_superuser:
        return redirect("home")
    return redirect("dashboard")


@login_required
@user_passes_test(is_user_admin)
def user_role_admin_view(request):
    # allows user_admins to change the roles of other users between member and officer
    if request.method == "POST":
        uid = request.POST.get("user_id")
        new_role = request.POST.get("new_role")
        # validate inputs
        if not uid or new_role not in (Profile.ROLE_MEMBER, Profile.ROLE_OFFICER):
            django_messages.error(request, "Invalid role change.")
            return redirect("user_role_admin")
        try:
            target = User.objects.select_related("profile").get(pk=uid)
        except User.DoesNotExist:
            django_messages.error(request, "User not found.")
            return redirect("user_role_admin")
        if not hasattr(target, "profile"):
            django_messages.error(request, "That user has no profile yet.")
            return redirect("user_role_admin")
        if target.profile.role == Profile.ROLE_USER_ADMIN:
            django_messages.error(
                request,
                "User administrator accounts cannot be changed in the application.",
            )
            return redirect("user_role_admin")
        target.profile.role = new_role
        target.profile.save(update_fields=["role"])
        django_messages.success(
            request,
            f"Updated {target.username} to {target.profile.get_role_display()}.",
        )
        return redirect("user_role_admin")
    # display all users and their roles for management, with access restricted to user_admins
    users = User.objects.select_related("profile").order_by("username")
    return render(request, "user_role_admin.html", {"users": users})


@login_required
def announcements_view(request):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    
    # only show active announcements, and show edit/delete options only to officers and execs
    announcements = Announcement.objects.filter(is_active=True)
    return render(
        request,
        "announcements.html",
        {"announcements": announcements, "nav_active": "announcements"},
    )


@login_required
@require_http_methods(["POST"])
def create_announcement(request):
    user = request.user
    # only officers and execs can create announcements
    if not (is_officer(user) or user.is_superuser):
        return JsonResponse(
            {"error": "Only club leaders can create announcements"}, status=403
        )

    try:
        data = json.loads(request.body)
        title = data.get("title")
        content = data.get("content")

        if not title or not content:
            return JsonResponse({"error": "Title and content required"}, status=400)

        announcement = Announcement.objects.create(
            author=request.user,
            title=title,
            content=content,
        )

        from .consumers import announcement_consumers # WebSocket consumers to broadcast new announcement in real-time to connected clients

        broadcast_message = {
            "type": "announcement_message",
            "id": announcement.id,
            "title": announcement.title,
            "content": announcement.content,
            "author": announcement.author.username,
            "created_at": announcement.created_at.isoformat(),
        }

        import asyncio # used to run async broadcast function that sends the new announcement to all connected WebSocket clients

        async def broadcast():
            for consumer in announcement_consumers:
                await consumer.announcement_message(broadcast_message)

        try:
            asyncio.run(broadcast())
        except RuntimeError:
            from asgiref.sync import async_to_sync

            async_to_sync(broadcast)()
        # return the created announcement as JSON response for frontend to update UI, including author username and created_at timestamp
        return JsonResponse(
            {
                "id": announcement.id,
                "title": announcement.title,
                "content": announcement.content,
                "author": announcement.author.username,
                "created_at": announcement.created_at.isoformat(),
            }
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@login_required
def get_announcements(request):
    announcements = Announcement.objects.filter(is_active=True).values(
        "id", "title", "content", "content", "author__username", "created_at"
    )
    return JsonResponse(list(announcements), safe=False)


@login_required
@user_passes_test(is_privileged)
def event_edit_view(request, event_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    ev = get_object_or_404(Event, pk=event_id) # fetch event or return 404 if not found
    error = None
    # displays fields for editing an existing event, and handles validation and saving of that event
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        start_dt = _parse_dt_local(request.POST.get("start_time", "").strip())
        end_dt = _parse_dt_local(request.POST.get("end_time", "").strip())
        location = request.POST.get("location", "").strip()
        event_type = request.POST.get("event_type", "").strip()
        description = request.POST.get("description", "").strip()
        if not title or not start_dt or not end_dt:
            error = "Title, start time, and end time are required."
        elif end_dt <= start_dt:
            error = "End time must be after start time."
        else: # validate that start and end times are not in the past, and if valid, save changes to the event
            error = _validate_event_not_in_past(start_dt, end_dt)
            if error is None:
                ev.title = title
                ev.start_time = start_dt
                ev.end_time = end_dt
                ev.location = location[:200]
                ev.event_type = event_type[:32]
                ev.description = description
                ev.save(update_fields=["title", "start_time", "end_time", "location", "event_type", "description"])
                django_messages.success(request, "Event updated.")
                return redirect("calendar")

    return render(
        request,
        "edit_event.html",
        {"nav_active": "calendar", "event": ev, "error": error},
    )


@login_required
@user_passes_test(is_privileged)
@require_http_methods(["POST"])
def event_delete_view(request, event_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    ev = get_object_or_404(Event, pk=event_id)
    ev.delete()
    django_messages.success(request, "Event deleted.")
    return redirect("calendar")


@login_required
@user_passes_test(is_privileged)
def announcement_edit_view(request, announcement_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    ann = get_object_or_404(Announcement, pk=announcement_id)
    error = None
    # displays fields for editing an existing announcement, and handles validation and saving of that announcement
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        if not title or not content:
            error = "Title and content are required."
        else:
            ann.title = title[:200]
            ann.content = content
            ann.save(update_fields=["title", "content"])
            django_messages.success(request, "Announcement updated.")
            return redirect("announcements")
    return render(
        request,
        "edit_announcement.html",
        {"nav_active": "announcements", "announcement": ann, "error": error},
    )


@login_required
@user_passes_test(is_privileged)
@require_http_methods(["POST"])
def announcement_delete_view(request, announcement_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    # handles deletion of an announcement, with access restricted to officers and execs
    ann = get_object_or_404(Announcement, pk=announcement_id)
    ann.delete()
    django_messages.success(request, "Announcement deleted.")
    return redirect("announcements")


@login_required
@user_passes_test(is_privileged)
def document_edit_view(request, document_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    doc = get_object_or_404(ClubDocument, pk=document_id)
    error = None
    if request.method == "POST": # allows editing title / file of existing document
        title = request.POST.get("title", "").strip()
        upload = request.FILES.get("file")
        if not title:
            error = "Title is required."
        else:
            doc.title = title[:200]
            if upload:
                max_bytes = 15 * 1024 * 1024
                if upload.size > max_bytes:
                    error = "File must be 15MB or smaller."
                else:
                    doc.file = upload
            if not error:
                doc.save()
                django_messages.success(request, "Document updated.")
                return redirect("documents")
    return render(
        request,
        "edit_document.html",
        {"nav_active": "documents", "document": doc, "error": error},
    )


@login_required
@user_passes_test(is_privileged)
@require_http_methods(["POST"])
def document_delete_view(request, document_id: int):
    if is_user_admin(request.user):
        return redirect("user_role_admin")
    doc = get_object_or_404(ClubDocument, pk=document_id)
    doc.delete()
    django_messages.success(request, "Document deleted.")
    return redirect("documents")
