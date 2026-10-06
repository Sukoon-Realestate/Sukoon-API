import 'dart:developer';
import 'dart:io';

import 'package:nsfw_detector_flutter/nsfw_detector_flutter.dart';

class NsfwDetectorHelper{
  static final NsfwDetector instance = NsfwDetector.instance;
  static Future<void> init()async{
    await NsfwDetector.initialize(threshold: 0.3);
    log('is initialized ${NsfwDetector.isInitialized}');
  }

  static Future<bool?> isSafe(File image)async{
    final result = await NsfwDetector.instance.detectNSFWFromBytes(image.readAsBytesSync());
    log('is Nsfw ${!result!.isNsfw}');
    log('is safe ${result.score}');
    return !result.isNsfw;
  }

  static void terminate(){
    NsfwDetector.disposeInstance();
  }
}