import 'dart:async';
import 'dart:developer';
import 'dart:io';
import 'package:flutter_phoenix/flutter_phoenix.dart';
import 'package:image_cropper/image_cropper.dart';
import 'package:lottie/lottie.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:share_plus/share_plus.dart';

import '../../config/language/languages.dart';
import '../../config/language/locale_keys.g.dart';
import '../../config/res/config_imports.dart';
import '../../generated/assets.dart';
import '../extensions/padding_extension.dart';
import '../navigation/navigator.dart';
import '../widgets/app_bottom_sheet.dart';
import '../widgets/custom_loading.dart';
import '../widgets/custom_messages.dart';
import 'nsfw_detector.dart';
import 'permission_handler/handler.dart';
import 'permission_handler/model.dart';

enum AppFlavor{dev, production, none}
extension Check on AppFlavor{
  bool get isDev => this == AppFlavor.dev;
  bool get isProduction => this == AppFlavor.production;
}


class Helpers {
  static String get getBundleId{
    if(currentFlavor.isDev){
      return ConstantManager.devBundleId;
    }
    return ConstantManager.bundleId;
  }

  static late AppFlavor currentFlavor;
  static Future<void> get getCurrentFlavor async{
    final PackageInfo packageInfo = await PackageInfo.fromPlatform();

    log('info is ${packageInfo.packageName} ${packageInfo.appName}');
    switch(packageInfo.packageName){
      case ConstantManager.devBundleId:
        currentFlavor = AppFlavor.dev;

      case ConstantManager.bundleId:
        currentFlavor = AppFlavor.production;

      default:
        currentFlavor = AppFlavor.none;
    }
  }


  static void showRestartSheet()async{
    AppBottomSheet.large(
        asyncCall: (context) async => await Phoenix.rebirth(context),
        btnTitle: LocaleKeys.updateAvailableUpdateNow,
        upperWidget: Lottie.asset(Assets)
    );
  }

  static String get deviceType => Platform.isAndroid? 'android' : 'ios';

  static Alignment get getAlignment {
    if (Languages.currentLanguage == Languages.arabic) {
      return Alignment.topRight;
    } else {
      return Alignment.topLeft;
    }
  }

  static Future<File?> getImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    if (image != null) {
      final File imageFile = File(image.path);
      return imageFile;
    }
    return null;
  }

  static Future<List<File>> getImages() async {
    final ImagePicker picker = ImagePicker();
    final List<XFile> result = await picker.pickMultiImage();
    if (result.isNotEmpty) {
      final List<File> files = result.map((e) => File(e.path)).toList();
      return files;
    } else {
      return [];
    }
  }

  static void changeStatusbarColor({
    required Color statusBarColor,
    Brightness? statusBarIconBrightness,
  }) {
    return SystemChrome.setSystemUIOverlayStyle(
      SystemUiOverlayStyle(
        statusBarColor: statusBarColor,
        statusBarIconBrightness: statusBarIconBrightness ?? Brightness.dark,
        systemNavigationBarColor: AppColors.main,
      ),
    );
  }

  static Future<void> checkPermission(
    Permission permission, {
    required FutureOr<void> Function(Permission permission)? onGranted,
    required FutureOr<void> Function(Permission permission)? onDenied,
    FutureOr<void> Function(Permission permission)? onDeniedForever,
    FutureOr<void> Function(Permission permission)? onLimited,
    bool openSettingsOnPermanentDenial = false,
  }) async {
    await PermissionHandler().checkPermission(
      openSetting: openSettingsOnPermanentDenial,
        permissionManagerModel: PermissionModel(
      permissions: [permission],
      onGranted: onGranted,
      onDenied: onDenied,
      onDeniedForever: onDeniedForever ?? onDenied,
      onPermissionLimited: onLimited ?? onGranted,
    ));
  }


  static Future<File?> _cropImage({required String sourcePath}) async {
    final CroppedFile? croppedFile = await ImageCropper().cropImage(
      sourcePath: sourcePath,
      uiSettings: [
        AndroidUiSettings(
          toolbarTitle: 'Cropper',
          toolbarColor: AppColors.primary,
          toolbarWidgetColor: Colors.white,
          statusBarColor: AppColors.primary,
          activeControlsWidgetColor: AppColors.primary,
          aspectRatioPresets: [
            CropAspectRatioPreset.original,
            CropAspectRatioPreset.square,
            CropAspectRatioPresetCustom(),
          ],
        ),
        IOSUiSettings(
          title: 'Cropper',
          aspectRatioPresets: [
            CropAspectRatioPreset.original,
            CropAspectRatioPreset.square,
            CropAspectRatioPresetCustom(),
          ],
        ),
      ],
    );
    return croppedFile != null ? File(croppedFile.path) : null;
  }

  static Future<File?> getImageFromCameraOrDevice() async {
    final ImagePicker picker = ImagePicker();
    File? image;
    await showModalBottomSheet(
        context: Go.navigatorKey.currentContext!,
        builder: (BuildContext bc) {
          return SafeArea(
            child: Wrap(
              children: <Widget>[
                ListTile(
                  leading: const Icon(Icons.photo_library),
                  title: Text(LocaleKeys.photoLibrary),
                  onTap: () async {
                    checkPermission(
                      Platform.isIOS?
                      Permission.storage :
                      Permission.photos,
                      onGranted: (permission) async {
                        final currentImage = await picker.pickImage(source: ImageSource.gallery);
                        if (currentImage != null) {
                          final croppedImage = await _cropImage(sourcePath: currentImage.path);
                          if(croppedImage != null){
                            final bool isSafe = await NsfwDetectorHelper.isSafe(croppedImage)??false;
                            if(isSafe){
                              image = File(croppedImage.path);
                            }else{
                              MessageUtils.showSnackBar(
                                  LocaleKeys.thisImageHasSensitiveContentPleaseRechooseAnotherImage);
                            }
                          }
                        }
                        Go.back();
                      },
                      onDenied: (permission) {
                        MessageUtils.showSnackBar(
                            LocaleKeys.unableToAccessPhotosPleaseOpenIt);
                      },
                      onDeniedForever: (permission) {
                        MessageUtils.showSnackBar(
                            LocaleKeys.unableToAccessPhotosPleaseOpenIt);
                        openAppSettings();
                      },
                      onLimited: (permission) async {
                        // iOS limited photo access - treat as granted
                        final currentImage = await picker.pickImage(source: ImageSource.gallery);
                        if (currentImage != null) {
                          final croppedImage = await _cropImage(sourcePath: currentImage.path);
                          if(croppedImage != null){
                            final bool isSafe = await NsfwDetectorHelper.isSafe(croppedImage)??false;
                            if(isSafe){
                              image = File(croppedImage.path);
                            }else{
                              MessageUtils.showSnackBar(
                                  LocaleKeys.thisImageHasSensitiveContentPleaseRechooseAnotherImage);
                            }
                          }
                        }
                        Go.back();
                      },
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.photo_camera),
                  title: Text(LocaleKeys.camera),
                  onTap: () async {
                    checkPermission(
                      Permission.camera,
                      onGranted: (permission) async {
                        final currentImage =
                            await picker.pickImage(source: ImageSource.camera);
                        if (currentImage != null) {
                          final croppedImage = await _cropImage(sourcePath: currentImage.path);
                          if(croppedImage != null){
                            final bool isSafe = await NsfwDetectorHelper.isSafe(croppedImage)??false;
                            if(isSafe){
                              image = File(croppedImage.path);
                            }else{
                              MessageUtils.showSnackBar(
                                  LocaleKeys.thisImageHasSensitiveContentPleaseRechooseAnotherImage);
                            }
                          }
                        }
                        Go.back();
                      },
                      onDenied: (permission) {
                        MessageUtils.showSnackBar(
                            LocaleKeys.unableToAccessCameraPleaseOpenIt);
                      },
                      onDeniedForever: (permission) {
                        MessageUtils.showSnackBar(
                            LocaleKeys.unableToAccessCameraPleaseOpenIt);
                        openAppSettings();
                      },
                    );
                  },
                ),
              ],
            ).paddingAll(AppPadding.pH10),
          );
        });
    return image;
  }

  static void shareApp(String url) {
    CustomLoading.showFullScreenLoading();
    final ShareParams params = ShareParams(uri: Uri.parse(url));
    SharePlus.instance.share(params).whenComplete(() {
      CustomLoading.hideFullScreenLoading();
    });
  }

  static String getDeviceType() {
    if (Platform.isIOS) {
      return 'ios';
    } else {
      return 'android';
    }
  }

  static String showByLang({
    required String ar,
    required String en,
  }) {
    if (Languages.currentLanguage.languageCode == 'ar') {
      return ar;
    } else {
      return en;
    }
  }
}

class CropAspectRatioPresetCustom implements CropAspectRatioPresetData {
  @override
  (int, int)? get data => (324, 214);

  @override
  String get name => '324 x 214 (3:2) Customized';
}