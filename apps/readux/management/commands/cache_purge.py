"""
Management command to purge one or more image identifiers from the
Cantaloupe image server cache and invalidate the corresponding paths
in CloudFront.
"""
import base64
import json
import logging
import sys
import uuid

import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.iiif.manifests.models import Manifest

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Usage:
        python manage.py cache_purge IMAGE_ID [IMAGE_ID ...]
        python manage.py cache_purge --file /path/to/ids.txt
        cat ids.txt | python manage.py cache_purge --file -

    Settings required (e.g. in local_settings.py):
        CANTALOUPE_URL = "https://images.example.org/"
        CANTALOUPE_SECRET_NAME = "cantaloupe"  # Secrets Manager secret name or ARN
        CLOUDFRONT_DISTRIBUTIONS = ["YYYYYYYY", "ZZZZZZZ"]

    The Secrets Manager secret is expected to be a JSON object with
    "api-username" and "api-secret" keys (matching the same secret the
    Cantaloupe ECS task pulls "api-username"/"api-secret" from).
    """

    help = "Purge image IDs from the Cantaloupe cache and invalidate the matching CloudFront paths."

    def add_arguments(self, parser):
        parser.add_argument(
            "image_ids",
            nargs="*",
            help="One or more Cantaloupe image identifiers to purge.",
        )
        parser.add_argument(
            "--file",
            help=(
                "Path to a file containing one image ID per line. "
                "Use '-' to read from stdin. Combined with any IDs given "
                "as positional arguments."
            ),
        )
        parser.add_argument(
            "--skip-cantaloupe",
            action="store_true",
            help="Skip the Cantaloupe purge step and only invalidate CloudFront.",
        )
        parser.add_argument(
            "--skip-cloudfront",
            action="store_true",
            help="Skip the CloudFront invalidation step and only purge Cantaloupe.",
        )

    def handle(self, *args, **options):
        image_ids = list(options["image_ids"])

        if options.get("file"):
            image_ids.extend(self._read_ids_from_file(options["file"]))

        # De-dupe while preserving order.
        seen = set()
        image_ids = [i for i in image_ids if not (i in seen or seen.add(i))]

        if not image_ids:
            raise CommandError(
                "No image IDs provided. Pass them as arguments or via --file."
            )

        cantaloupe_url = getattr(settings, "CANTALOUPE_URL", None)
        secret_name = getattr(settings, "CANTALOUPE_SECRET_NAME", None)
        distributions = getattr(settings, "CLOUDFRONT_DISTRIBUTIONS", None)

        auth_header = None
        if not options["skip_cantaloupe"]:
            if not (cantaloupe_url and secret_name):
                raise CommandError(
                    "CANTALOUPE_URL and CANTALOUPE_SECRET_NAME must be set to purge "
                    "Cantaloupe (or pass --skip-cantaloupe)."
                )
            auth_header = self._get_basic_auth_header(secret_name)

        if not options["skip_cloudfront"] and not distributions:
            raise CommandError(
                "CLOUDFRONT_DISTRIBUTIONS must be set to invalidate CloudFront "
                "(or pass --skip-cloudfront)."
            )

        cloudfront_client = None
        if not options["skip_cloudfront"]:
            cloudfront_client = boto3.client("cloudfront")

        failures = []

        for image_id in image_ids:
            self.stdout.write(f"Processing {image_id}...")

            if not options["skip_cantaloupe"]:
                manifest = Manifest.objects.get(pid=image_id)

                for canvas in manifest.canvas_set.all():
                    ok = self._purge_cantaloupe(cantaloupe_url, auth_header, canvas.pid)
                    if not ok:
                        failures.append(canvas.pid)

            if not options["skip_cloudfront"]:
                ok = self._invalidate_cloudfront(
                    cloudfront_client, distributions, image_id
                )
                if not ok:
                    failures.append(image_id)

        if failures:
            raise CommandError(
                f"Completed with errors for: {', '.join(sorted(set(failures)))}"
            )

        self.stdout.write(
            self.style.SUCCESS(f"Done. Processed {len(image_ids)} image(s).")
        )

    def _read_ids_from_file(self, path):
        if path == "-":
            lines = sys.stdin.readlines()
        else:
            try:
                with open(path, encoding="utf8") as f:
                    lines = f.readlines()
            except OSError as e:
                raise CommandError(f"Could not read file {path}: {e}") from e

        return [line.strip() for line in lines if line.strip()]

    def _get_basic_auth_header(self, secret_name):
        """
        Fetches the Cantaloupe credentials from AWS Secrets Manager and
        returns a ready-to-use "Basic <base64>" header value. The secret
        is expected to be a JSON object with "api-username" and
        "api-secret" keys.
        """
        client = boto3.client("secretsmanager")

        try:
            response = client.get_secret_value(SecretId=secret_name)
        except (BotoCoreError, ClientError) as e:
            raise CommandError(f"Could not retrieve secret '{secret_name}': {e}") from e

        try:
            secret = json.loads(response["SecretString"])
            username = secret["api-username"]
            password = secret["api-secret"]
        except (KeyError, ValueError) as e:
            raise CommandError(
                f"Secret '{secret_name}' is not in the expected format "
                f"(JSON with 'api-username' and 'api-secret' keys): {e}"
            ) from e

        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {token}"

    def _purge_cantaloupe(self, cantaloupe_url, auth_header, image_id):
        """
        Sends a POST request to the Cantaloupe tasks endpoint to purge a
        single item from cache. Returns True on success, False on failure.
        """
        endpoint = f"{cantaloupe_url}/tasks"
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
        }
        
        payload = {"verb": "PurgeItemFromCache", "identifier": image_id}

        try:
            response = requests.post(
                endpoint, headers=headers, json=payload, timeout=30
            )
        except requests.exceptions.RequestException as e:
            logger.error("Cantaloupe purge request failed for %s: %s", image_id, e)
            self.stderr.write(self.style.ERROR(f"[{image_id}] Connection error: {e}"))
            return False

        # Cantaloupe returns 202 Accepted if the task is queued.
        if response.status_code in (200, 201, 202):
            logger.info(
                "Cantaloupe purge queued for %s (%s)", image_id, response.status_code
            )
            self.stdout.write(f"  Cantaloupe: purge queued ({response.status_code})")
            return True
        elif response.status_code == 401:
            logger.error("Cantaloupe purge unauthorized for %s", image_id)
            self.stderr.write(
                self.style.ERROR(f"[{image_id}] Unauthorized: check API token.")
            )
            return False
        else:
            logger.error(
                "Cantaloupe purge failed for %s: %s %s",
                image_id,
                response.status_code,
                response.text,
            )
            self.stderr.write(
                self.style.ERROR(
                    f"[{image_id}] Cantaloupe failed: {response.status_code} - {response.text}"
                )
            )
            return False

    def _invalidate_cloudfront(self, client, distributions, image_id):
        """
        Creates a CloudFront invalidation for the given image ID across all
        configured distributions. Returns True if all invalidations were
        created successfully, False if any failed.
        """
        paths = [f"/iiif/2/{image_id}*", f"/iiif/3/{image_id}*"]
        success = True

        for distro in distributions:
            try:
                client.create_invalidation(
                    DistributionId=distro,
                    InvalidationBatch={
                        "Paths": {"Quantity": len(paths), "Items": paths},
                        "CallerReference": str(uuid.uuid4()),
                    },
                )
                logger.info(
                    "CloudFront invalidation created for %s on %s", image_id, distro
                )
                self.stdout.write(f"  CloudFront: invalidation created on {distro}")
            except (BotoCoreError, ClientError) as e:
                logger.error(
                    "CloudFront invalidation failed for %s on %s: %s",
                    image_id,
                    distro,
                    e,
                )
                self.stderr.write(
                    self.style.ERROR(f"[{image_id}] CloudFront failed on {distro}: {e}")
                )
                success = False

        return success
