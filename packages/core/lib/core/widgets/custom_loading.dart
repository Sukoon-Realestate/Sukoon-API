import 'package:flutter/material.dart';
import 'package:flutter_spinkit/flutter_spinkit.dart';

import '../../config/res/config_imports.dart';
import '../helpers/loading_manager.dart';

class CustomLoading {
  static Center showLoadingView({Color? color, double? size}) {
    return Center(
      child: SpinKitCircle(
        color: color ?? AppColors.primary,
        size: size ?? AppSize.sH25,
      ),
    );
  }

  static void showFullScreenLoading() => FullScreenLoadingManager.show();

  static void hideFullScreenLoading() => FullScreenLoadingManager.hide();
  static void manageFullScreenLoading(Future<void> Function() call) {
    CustomLoading.showFullScreenLoading();
    CustomLoading.hideFullScreenLoading();
  }
}
