import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:toastification/toastification.dart';

import '../../../config/language/locale_keys.g.dart';
import '../../../config/res/config_imports.dart';
import '../../navigation/navigator.dart';
import '../../shared/base_state.dart';
import '../app_text.dart';

class Messages {
  static ToastificationItem showToast({
    required String msg,
    BaseStatus status = BaseStatus.success,
    String? title,
    Duration autoCloseDuration = const Duration(seconds: 4),
  }) {
    final _ToastDesign design = _ToastDesign.fromStatus(status);

    return Toastification().show(
      context: Go.context,
      overlayState: Go.navigatorKey.currentState?.overlay,
      alignment: Alignment.topCenter,
      animationDuration: const Duration(milliseconds: 220),
      autoCloseDuration: autoCloseDuration,
      type: design.type,
      style: ToastificationStyle.flat,
      title: AppText(
        title ?? design.title,
        color: AppColors.sokoonNavy,
        fontSize: 14.sp,
        fontWeight: FontWeight.w800,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      description: AppText(
        msg,
        color: AppColors.sokoonGray,
        fontSize: 12.sp,
        fontWeight: FontWeight.w500,
        maxLines: 3,
        overflow: TextOverflow.ellipsis,
        height: 1.25,
      ),
      icon: _ToastIcon(design: design),
      primaryColor: design.accentColor,
      backgroundColor: design.backgroundColor,
      foregroundColor: design.accentColor,
      padding: EdgeInsetsDirectional.fromSTEB(14.w, 12.h, 10.w, 12.h),
      margin: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
      borderRadius: BorderRadius.circular(16.r),
      borderSide: BorderSide(color: design.borderColor),
      boxShadow: const [
        BoxShadow(
          color: AppColors.shadowBlack04,
          offset: Offset(0, 2),
          blurRadius: 4,
        ),
      ],
      progressBarTheme: ProgressIndicatorThemeData(
        color: design.accentColor,
        linearMinHeight: 2.r,
        linearTrackColor: design.borderColor,
      ),
      closeButton: ToastCloseButton(
        showType: CloseButtonShowType.always,
        buttonBuilder: (context, onClose) => IconButton(
          onPressed: onClose,
          visualDensity: VisualDensity.compact,
          padding: EdgeInsets.zero,
          constraints: BoxConstraints.tight(Size(32.r, 32.r)),
          icon: Icon(
            Icons.close_rounded,
            color: AppColors.sokoonGray,
            size: 18.r,
          ),
        ),
      ),
      dragToClose: true,
      showIcon: true,
      dismissDirection: DismissDirection.horizontal,
      pauseOnHover: true,
      showProgressBar: true,
    );
  }
}

class _ToastIcon extends StatelessWidget {
  final _ToastDesign design;

  const _ToastIcon({required this.design});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 32.r,
      height: 32.r,
      decoration: BoxDecoration(
        color: design.iconBackgroundColor,
        borderRadius: BorderRadius.circular(12.r),
      ),
      child: Icon(design.icon, color: design.accentColor, size: 18.r),
    );
  }
}

class _ToastDesign {
  final String title;
  final Color accentColor;
  final Color backgroundColor;
  final Color borderColor;
  final Color iconBackgroundColor;
  final IconData icon;
  final ToastificationType type;

  const _ToastDesign({
    required this.title,
    required this.accentColor,
    required this.backgroundColor,
    required this.borderColor,
    required this.iconBackgroundColor,
    required this.icon,
    required this.type,
  });

  factory _ToastDesign.fromStatus(BaseStatus status) {
    switch (status) {
      case BaseStatus.success:
      case BaseStatus.loadingMore:
        return _ToastDesign(
          title: LocaleKeys.successDone,
          accentColor: AppColors.green,
          backgroundColor: AppColors.greenPale,
          borderColor: AppColors.greenAlpha19,
          iconBackgroundColor: AppColors.greenAlpha09,
          icon: Icons.check_rounded,
          type: const ToastificationType.custom(
            'sokoun_success',
            AppColors.green,
            Icons.check_rounded,
          ),
        );
      case BaseStatus.error:
        return _ToastDesign(
          title: LocaleKeys.operationFaild,
          accentColor: AppColors.sokoonRose,
          backgroundColor: AppColors.redPale,
          borderColor: AppColors.roseAlpha19,
          iconBackgroundColor: AppColors.roseAlpha07,
          icon: Icons.close_rounded,
          type: const ToastificationType.custom(
            'sokoun_error',
            AppColors.sokoonRose,
            Icons.close_rounded,
          ),
        );
      case BaseStatus.loading:
      case BaseStatus.initial:
        return _ToastDesign(
          title: ConstantManager.projectName,
          accentColor: AppColors.blue,
          backgroundColor: AppColors.bluePale,
          borderColor: AppColors.grayPale,
          iconBackgroundColor: AppColors.grayOffWhite,
          icon: Icons.info_outline_rounded,
          type: const ToastificationType.custom(
            'sokoun_info',
            AppColors.blue,
            Icons.info_outline_rounded,
          ),
        );
    }
  }
}
