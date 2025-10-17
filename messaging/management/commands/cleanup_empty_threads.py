from django.core.management.base import BaseCommand
from messaging.models import MessageThread
from django.db.models import Count

class Command(BaseCommand):
    help = 'Delete message threads that have no messages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        # Find threads with no messages
        empty_threads = MessageThread.objects.annotate(
            message_count=Count('messages')
        ).filter(message_count=0)
        
        count = empty_threads.count()
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING(
                    f'Would delete {count} empty message threads (dry run)'
                )
            )
            for thread in empty_threads:
                participants = ", ".join([user.username for user in thread.participants.all()])
                self.stdout.write(f"Thread {thread.id} (participants: {participants})")
            return

        if count > 0:
            empty_threads.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} empty message threads'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    'No empty message threads found'
                )
            )