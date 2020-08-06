from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse, JsonResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseGone,\
    HttpResponseNotFound

from .models import Student, Interview, AvailabilitySlot

import json
import datetime

class Constants:
    ERROR_METHOD_NOT_ALLOWED = "method not allowed"
    ERROR_MAX_INTERVIEWS_EXCEEDS = "max interviews exhausted"
    ERROR_MAX_BAD_INTERVIEWS = "too many bad interviews"
    ERROR_NO_SLOTS = "no slots available"
    MAX_INTERVIEWS_ALLOWED = 15
    GRADE_UNGRADED = -1

# Create your views here.
def handle_ping(request):
    return HttpResponse("pong")

def grade_flunked(query_result):
    if query_result == Constants.GRADE_UNGRADED:
        return False
    if query_result.grade > 1:
        return False
    return True

def parse_req_body(body: str):
    booking_req = json.loads(body)
    if "studentId" not in booking_req or "startDateTime" not in booking_req or "endDateTime" not in booking_req:
        raise Exception("missing params")
    start = datetime.datetime.fromisoformat(booking_req["startDateTime"])
    end = datetime.datetime.fromisoformat(booking_req["endDateTime"])
    student = get_object_or_404(Student, pk=booking_req["studentId"])
    return (student, start, end)

@transaction.atomic
def book_time_slot(slot: AvailabilitySlot, student: Student, student_start: datetime, student_end: datetime) -> str:
    """
    Given a query set of AvailabilitySlots book a time slot atomically
    - Create before and after time slots of the trainer whose slot is being booked
    - Create an interview item in database to signify that an interview was booked
    - Delete the selected slot from availability database
    - Return the trainer name
    """
    locked_slot = AvailabilitySlot.objects.select_for_update().get(pk=slot.id)
    trainer = locked_slot.trainer
    trainer_name = str(trainer)
    if locked_slot.fromTime != student_start:
        before_slot = AvailabilitySlot(fromTime=locked_slot.fromTime, toTime=student_start, trainer=trainer)
        before_slot.save()
    if locked_slot.toTime != student_end:
        after_slot = AvailabilitySlot(fromTime=student_end, toTime=locked_slot.toTime, trainer=trainer)
        after_slot.save()
    iv = Interview(student=student, trainer=trainer, fromTime=student_start, toTime=student_end, grade=Constants.GRADE_UNGRADED)
    iv.save()
    locked_slot.delete()
    return trainer_name

def handle_interview_request(request):
    """
    sample data format:
    {
        ‘studentId’: 123,
        “startDateTime: 2020-06-05T13:00:00’,
        “endDateTime”: ‘2020-06-05T14:00:00’,
    }
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(Constants.ERROR_METHOD_NOT_ALLOWED)
    try:
        student, start, end = parse_req_body(request.body)
    except Exception as e:
        return HttpResponseBadRequest(e)
    interviews = Interview.objects.filter(student=student,toTime__lt=datetime.datetime.now(tz=timezone.utc))\
        .order_by("-toTime")[:Constants.MAX_INTERVIEWS_ALLOWED]
    total_interviews = interviews.count()
    if total_interviews == Constants.MAX_INTERVIEWS_ALLOWED:
        return HttpResponseGone(Constants.ERROR_MAX_INTERVIEWS_EXCEEDS)
    if total_interviews >= 2 and grade_flunked(interviews[0]) and grade_flunked(interviews[1]):
        return HttpResponseGone(Constants.ERROR_MAX_BAD_INTERVIEWS)
    previous_interviewers = []
    result = AvailabilitySlot.objects.filter(fromTime__lte=start, toTime__gte=end).exclude(trainer__in=interviews.values_list('trainer', flat=True))
    if len(result) == 0:
        return HttpResponseNotFound(Constants.ERROR_NO_SLOTS)
    return JsonResponse({"trainer": book_time_slot(result[0], student, start, end)})
