from celery import shared_task
from django.utils import timezone
from .models import Message

@shared_task
def delete_message_task(message_id: int):
    # Hard-delete specific message
    Message.objects.filter(id=message_id).delete()

@shared_task
def delete_overdue_messages_task():
    # Safety sweep: delete any messages past their delete_after deadline
    Message.objects.filter(
        delete_after__isnull=False,
        delete_after__lte=timezone.now()
    ).delete()
