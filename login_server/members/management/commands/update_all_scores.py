# login_server/members/management/commands/update_all_scores.py

from django.core.management.base import BaseCommand
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates scores for all user profiles using the ML model'

    def handle(self, *args, **kwargs):
        try:
            # Get the UserProfile model dynamically
            UserProfile = apps.get_model('members', 'UserProfile')

            # Get all profiles
            profiles = UserProfile.objects.all()

            # Initialize counters
            total = profiles.count()
            updated = 0
            failed = 0

            self.stdout.write(f"Starting score update for {total} profiles...")

            # Update each profile
            for profile in profiles:
                try:
                    old_score = profile.score
                    profile.update_score()
                    new_score = profile.score

                    self.stdout.write(
                        f"Updated {profile.user.username}: {old_score:.1f} -> {new_score:.1f}"
                    )
                    updated += 1

                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to update score for {profile.user.username}: {str(e)}")

            # Print summary
            self.stdout.write(self.style.SUCCESS(
                f"\nScore update complete:\n"
                f"Total profiles: {total}\n"
                f"Successfully updated: {updated}\n"
                f"Failed: {failed}"
            ))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Fatal error during score update: {str(e)}")
            )