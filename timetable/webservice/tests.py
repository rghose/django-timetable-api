from django.test import TestCase
from django.test.client import RequestFactory

from .views import handle_interview_request, Constants
from .models import Student, Trainer, Interview, AvailabilitySlot

import json
import datetime

# Create your tests here.
class InterviewRequest(TestCase):
    def test_invalid_http_get(self):
        rf = RequestFactory()
        request = rf.get('/api/interview')
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 405)

    def test_invalid_http_put(self):
        rf = RequestFactory()
        request = rf.put('/api/interview')
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 405)

    def test_invalid_body_data(self):
        rf = RequestFactory()
        request = rf.post('/api/interview',content_type='application/json', data="")
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)

    def test_empty_data(self):
        rf = RequestFactory()
        request = rf.post('/api/interview',content_type='application/json', data="{}")
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)
    
    def test_missing_param_1(self):
        rf = RequestFactory()
        data={"startDateTime": "2020-06-05T13:00:00", "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)

    def test_missing_param_2(self):
        rf = RequestFactory()
        data={"studentId": 1, "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)

    def test_missing_param_3(self):
        rf = RequestFactory()
        data={"studentId": 1, "startDateTime": "2020-06-05T13:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)
    
    def test_invalid_dates(self):
        rf = RequestFactory()
        data={"studentId": 1, "startDateTime": "5 June 2020 3 PM", "endDateTime": "5 June 2020 4 PM" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)

    def test_valid_data_no_student(self):
        rf = RequestFactory()
        data={"studentId": 1, "startDateTime": "2020-06-05T13:00:00", "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 400)

class InterviewRequestWithMockData(TestCase):
    def test_valid_data_no_slots(self):
        s = Student(name="test")
        s.save()
        rf = RequestFactory()
        data={"studentId": s.id, "startDateTime": "2020-06-05T13:00:00", "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), Constants.ERROR_NO_SLOTS)

    def test_max_interviews_exceeded(self):
        old_value_max_interviews = Constants.MAX_INTERVIEWS_ALLOWED
        Constants.MAX_INTERVIEWS_ALLOWED = 3
        s = Student(name="test")
        s.save()
        t = Trainer(name="a")
        t.save()
        for i in range(0,Constants.MAX_INTERVIEWS_ALLOWED):
            f = datetime.datetime.fromisoformat("2020-05-01T13:00:00")
            e = datetime.datetime.fromisoformat("2020-05-01T14:00:00")
            i1 = Interview(student=s, trainer=t, grade=-1, fromTime=f, toTime=e)
            i1.save()
        rf = RequestFactory()
        data={"studentId": s.id, "startDateTime": "2020-06-05T13:00:00", "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 410)
        self.assertEqual(str(response.content.decode()), Constants.ERROR_MAX_INTERVIEWS_EXCEEDS)
        Constants.MAX_INTERVIEWS_ALLOWED = old_value_max_interviews

    def test_max_tests_flunked(self):
        s = Student(name="test2")
        s.save()
        t = Trainer(name="trainer2")
        t.save()
        for i in range(0,2):
            f = datetime.datetime.fromisoformat("2020-05-01T13:00:00")
            e = datetime.datetime.fromisoformat("2020-05-01T14:00:00")
            iv = Interview(student=s, trainer=t, grade=0, fromTime=f, toTime=e)
            iv.save()
        rf = RequestFactory()
        data={"studentId": s.id, "startDateTime": "2020-06-05T13:00:00", "endDateTime": "2020-06-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 410)
        self.assertEqual(str(response.content.decode()), Constants.ERROR_MAX_BAD_INTERVIEWS)
    
    def test_student_with_previous_interviews_from_other_trainers(self):
        s = Student(name="student")
        s.save()
        for i in range(0,4):
            t = Trainer(name="trainer{}".format(i))
            t.save()
            f = datetime.datetime.fromisoformat("2020-05-01T13:00:00")
            e = datetime.datetime.fromisoformat("2020-05-01T14:00:00")
            iv = Interview(student=s, trainer=t, grade=2, fromTime=f, toTime=e)
            iv.save()
            fa = datetime.datetime.fromisoformat("2020-08-05T10:00:00")
            ta = datetime.datetime.fromisoformat("2020-08-05T20:00:00")
            a = AvailabilitySlot(trainer=t, fromTime=fa, toTime=ta)
            a.save()
        rf = RequestFactory()
        data={"studentId": s.id, "startDateTime": "2020-08-05T13:00:00", "endDateTime": "2020-08-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), Constants.ERROR_NO_SLOTS)

    def test_student_with_new_trainer_slot(self):
        s = Student(name="student")
        s.save()
        for i in range(0,4):
            t = Trainer(name="trainer{}".format(i))
            t.save()
            f = datetime.datetime.fromisoformat("2020-05-01T13:00:00")
            e = datetime.datetime.fromisoformat("2020-05-01T14:00:00")
            iv = Interview(student=s, trainer=t, grade=2, fromTime=f, toTime=e)
            iv.save()
            fa = datetime.datetime.fromisoformat("2020-08-05T10:00:00")
            ta = datetime.datetime.fromisoformat("2020-08-05T20:00:00")
            a = AvailabilitySlot(trainer=t, fromTime=fa, toTime=ta)
            a.save()
        trainer_name = "newTrainer"
        new_trainer = Trainer(name=trainer_name)
        new_trainer.save()
        fav = datetime.datetime.fromisoformat("2020-08-05T10:00:00")
        tav = datetime.datetime.fromisoformat("2020-08-05T20:00:00")
        av = AvailabilitySlot(trainer=new_trainer, fromTime=fav, toTime=tav)
        av.save()
        rf = RequestFactory()
        data={"studentId": s.id, "startDateTime": "2020-08-05T13:00:00", "endDateTime": "2020-08-05T14:00:00" }
        request = rf.post('/api/interview',content_type='application/json', data=json.dumps(data))
        response = handle_interview_request(request)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.content.decode())
        self.assertEqual(json_response["trainer"], trainer_name)
