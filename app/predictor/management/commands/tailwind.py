import subprocess
import sys
import time
from pathlib import Path

from django.core.management.base import CommandError
from tailwind.management.commands.tailwind import Command as TailwindCommand


class Command(TailwindCommand):
    """Ajoute l'alias historique `tailwind runserver` à django-tailwind 4."""

    def run_from_argv(self, argv):
        if len(argv) > 2 and argv[2] == "runserver":
            return self._run_windows_development_servers(argv[0])
        return super().run_from_argv(argv)

    def _run_windows_development_servers(self, manage_py):
        manage_path = Path(manage_py).resolve()
        commands = [
            [sys.executable, str(manage_path), "tailwind", "start"],
            [sys.executable, str(manage_path), "runserver"],
        ]
        self.stdout.write(self.style.SUCCESS(
            "Démarrage du watcher Tailwind et du serveur Django..."
        ))
        processes = [subprocess.Popen(command, cwd=manage_path.parent) for command in commands]
        try:
            while all(process.poll() is None for process in processes):
                time.sleep(0.5)
            failed = next((process for process in processes if process.returncode), None)
            if failed:
                raise CommandError(
                    f"Un processus de développement s'est arrêté avec le code {failed.returncode}."
                )
        except KeyboardInterrupt:
            self.stdout.write("\nArrêt du serveur Django et de Tailwind...")
        finally:
            for process in processes:
                if process.poll() is None:
                    process.terminate()
            for process in processes:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
