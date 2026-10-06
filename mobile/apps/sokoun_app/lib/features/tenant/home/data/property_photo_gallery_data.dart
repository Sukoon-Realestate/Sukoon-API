import 'dart:io';

import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import 'package:gal/gal.dart';

class PropertyPhotoGalleryData {
  PropertyPhotoGalleryData({
    Future<File> Function(String)? loadImage,
    Stream<FileResponse> Function(String)? loadImageStream,
  }) : _loadImage = loadImage,
       _loadImageStream = loadImageStream ?? _cachedImageStream;

  static const String albumName = 'سكون';

  final Future<File> Function(String)? _loadImage;
  final Stream<FileResponse> Function(String) _loadImageStream;

  static Stream<FileResponse> _cachedImageStream(String url) =>
      DefaultCacheManager().getFileStream(url, withProgress: true);

  Future<File> _download(String url, void Function(double?)? onProgress) async {
    final loadImage = _loadImage;
    if (loadImage != null) return loadImage(url);
    await for (final FileResponse event in _loadImageStream(url)) {
      if (event is DownloadProgress) {
        final int? total = event.totalSize;
        onProgress?.call(
          total != null && total > 0
              ? (event.downloaded / total).clamp(0.0, 1.0)
              : null,
        );
      } else if (event is FileInfo &&
          (event.source == FileSource.Online ||
              event.validTill.isAfter(DateTime.now()))) {
        return event.file;
      }
    }
    throw const FileSystemException('Image download did not complete.');
  }

  Future<bool> saveImage(
    String imageUrl, {
    void Function(double?)? onProgress,
  }) async {
    if (!await Gal.requestAccess(toAlbum: true)) return false;

    final File image = await _download(imageUrl, onProgress);
    // Writing to the gallery has no measurable byte progress.
    onProgress?.call(null);
    await Gal.putImageBytes(
      await image.readAsBytes(),
      album: albumName,
      name: 'sokoun_${DateTime.now().microsecondsSinceEpoch}',
    );
    return true;
  }
}
