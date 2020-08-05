from django.db import models

# Create your models here.
class Trainer(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return "%s" % (self.name)

class Student(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return "%s" % (self.name)

class Interview(models.Model):
    """
    If student or trainers are removed, keep the data
    this can be used for accountability purposes.
    """
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    trainer = models.ForeignKey(Trainer, on_delete=models.DO_NOTHING)
    grade = models.IntegerField()
    fromTime = models.DateTimeField()
    toTime = models.DateTimeField()
    def __str__(self):
        return "%s => %s on %s" % (self.trainer.name, self.student.name, self.fromTime)

class AvailabilitySlot(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    fromTime = models.DateTimeField()
    toTime = models.DateTimeField()
    def __str__(self):
        return "%s on %s - %s" % (self.trainer.name, self.fromTime, self.toTime)
