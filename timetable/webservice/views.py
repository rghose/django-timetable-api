from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse, JsonResponse, \
    HttpResponseNotAllowed, HttpResponseBadRequest, HttpResponseGone

from .models import Student, Interview, AvailabilitySlot

import json
import datetime

class Constants:
    ERROR_METHOD_NOT_ALLOWED = "method not allowed"
    ERROR_MAX_INTERVIEWS_EXCEEDS = "max interviews exhausted"
    ERROR_MAX_BAD_INTERVIEWS = "too many bad interviews"
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
    confirmed = False
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
    if total_interviews >= 1:
        print("interviews:",interviews)
        #previous_interviewers = interviews.trainer
    return JsonResponse({"interview": confirmed})
