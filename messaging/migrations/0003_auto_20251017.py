from django.db import migrations
from django.db.models import Count

def dedupe_empty_threads(apps, schema_editor):
    MessageThread = apps.get_model('messaging', 'MessageThread')
    # Get all threads
    for thread in MessageThread.objects.annotate(msg_count=Count('messages')).filter(msg_count=0):
        # For each thread participant
        participants = list(thread.participants.all().order_by('id'))
        if len(participants) != 2:  # Only handle 1:1 threads
            continue
        
        # Look for other empty threads with same participants
        dupes = (MessageThread.objects
                 .filter(participants__in=participants)
                 .annotate(msg_count=Count('messages'))
                 .filter(msg_count=0)
                 .distinct()
                 .order_by('id'))
        
        # Keep oldest thread, delete others
        first = None
        for t in dupes:
            if not first:
                first = t
                continue
            # Check if same participants
            t_parts = set(t.participants.all())
            first_parts = set(first.participants.all())
            if t_parts == first_parts:
                t.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_rename_body_message_enc_body'),
    ]

    operations = [
        migrations.RunPython(dedupe_empty_threads, migrations.RunPython.noop),
    ]