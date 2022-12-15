# Ingest Steps

## Local Ingest

A zip file containing a single volume and metadata file are uploaded.

### Options

- Image server
- Zip file

### Steps

1. Admin form is saved
   1. `Manifest` is created by `Apps.Ingest.services.create_manifest()`.
   2. The `Local` object is passed to teh `create_canvas_from_local_task` task.
2. `create_canvas_from_local_task()`
   1. Creates `Manifest` is missing.
   2. `create_canvases()` is called on the `Local` object.
      1. The zip file is streamed from S3 in chunks.
      2. Files that are not an image or OCR file are ignored.
      3. Image and OCR files are uploaded to the target image server's storage service.
      4. Lists of the uploaded image and OCR files are iterated through
         1. `Canvas` objects are created from the image files.
         2. If the image as an associated OCR file, the `Canvas` object is passed to teh `add_ocr_task` task.
   3. Each `Canvas` object is passed to an `ensure_dimensions` task.

## Bulk Ingest

Zip files of individual volumes are uploaded. Each zip file can include a metadata file or a single metadata file can be uploaded for all volumes.

### Options

- Image server
- Files
  - Zip files of individual volumes
  - Metadata file (optional)
- Collection (optional)

### Steps

1. Admin form is saved
    1. Metadata file is processed if present.
    2. A `Local` ingest object is created for each zip file.
    3. The zip file is saved as the `bundle_from_bulk` attribute on the `Local` object. This saves the zip file to the local file system. This is done so the person uploading this files does not have to wait for each file to be uploaded to S3.
    4. The `Local` object is passed to the `upload_to_s3_task` task
2. `upload_to_s3_task()`
   1. `Local.bundle_to_s2()`
      1. The `bundle_from_bulk` file object, which is on the local disk is assigned to the `Local` object's `bundle`. This uploads the file to S3 and deletes the local copy.
      2. The `Local` object is passed to the `create_canvas_from_local_task` task.
3. At this point, the bulk ingest process continues exactly as local ingest at step 2.
