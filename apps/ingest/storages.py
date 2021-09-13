from storages.backends.s3boto3 import S3Boto3Storage

class TmpStorage(S3Boto3Storage):
    bucket_name = 'readux'
    location = 'tmp'

class IngestStorage(S3Boto3Storage):
    bucket_name = 'readux-ingest'