from django.core.management.base import BaseCommand
from messaging.models import MessageThread

class Command(BaseCommand):
    help = 'Delete all message threads (development only)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        thread_count = MessageThread.objects.count()
        
        if thread_count == 0:
            self.stdout.write(self.style.SUCCESS('No threads to delete.'))
            return

        if not options['force']:
            confirm = input(f'This will delete {thread_count} threads and ALL their messages. Are you sure? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Cancelled.'))
                return

        # Delete all threads (will cascade to messages due to foreign key)
        MessageThread.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {thread_count} threads and their messages.'))