"""
Manage command to restart background tasks.
"""
from os import kill
from signal import SIGKILL
from subprocess import check_output, Popen
from django.core.management.base import BaseCommand
from background_task.models import CompletedTask

class Command(BaseCommand):
    """
    Manage command that looks up system pids for the background tasks and kills them.

    Finally, it starts three new processes for the background tasks.

    TODO: Instead of assuming all background processes have been locked by a completed task,
    we might should look to some other way to track the processes. The danger is that an
    outdated process will pickup a job and it will be hard to figure out why something
    bad happened.
    """
    def handle(self, *args, **options):
        pids = [task.locked_by for task in CompletedTask.objects.all()]
        for pid in pids:
            try:
                kill(pid, SIGKILL)
            except ProcessLookupError:
                pass

        python_path = check_output(['which', 'python']).decode('utf-8').rstrip()
        for _ in range(3):
            Popen(['nohup', python_path, 'manage.py', 'process_tasks'])
