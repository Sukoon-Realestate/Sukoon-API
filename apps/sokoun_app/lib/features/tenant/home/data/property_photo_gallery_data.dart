import 'dart:io';

import 'package:flutter_cache_manager/flutter_cache_manager.dart';
import 'package:gal/gal.dart';

class PropertyPhotoGalleryData {
  PropertyPhotoGalleryData({Future<File> Function(String)? loadImage})
    : _loadImage = loadImage ?? DefaultCacheManager().getSingleFile;

  static const String albumName = 'سكون';

  final Future<File> Function(String) _loadImage;

  Future<bool> saveImage(String imageUrl) async {
    if (!await Gal.requestAccess(toAlbum: true)) return false;

    final File image = await _loadImage(imageUrl);
    await Gal.putImageBytes(
      await image.readAsBytes(),
      album: albumName,
      name: 'sokoun_${DateTime.now().microsecondsSinceEpoch}',
    );
    return true;
  }
}
