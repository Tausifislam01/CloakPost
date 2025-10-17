from django.core.management.base import BaseCommand
from messaging.models import MessageThread
from django.db.models import Count

class Command(BaseCommand):
    help = 'Clean up empty message threads'

    def handle(self, *args, **kwargs):
        # Find threads with no messages
        empty_threads = MessageThread.objects.annotate(
            message_count=Count('messages')
        ).filter(message_count=0)
        
        count = empty_threads.count()
        empty_threads.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} empty threads')
        )