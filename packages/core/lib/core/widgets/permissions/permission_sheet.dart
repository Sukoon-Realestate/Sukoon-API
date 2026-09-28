import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/align_helper.dart';
import '../../extensions/padding_extension.dart';
import '../../extensions/sized_box_helper.dart';
import '../../navigation/navigator.dart';

/// The shared surface for the location and notification permission prompts.
class PermissionSheet extends StatelessWidget {
  const PermissionSheet({super.key, required this.child});

  final Widget child;

  /// Presents a prompt over the current screen, without requesting OS access.
  ///
  /// The prompt returns true to continue, false for "not now", or null when
  /// dismissed. Using the root route keeps dismissal through [Go] consistent.
  static Future<bool?> show({BuildContext? context, required Widget child}) {
    return showModalBottomSheet<bool>(
      context: context ?? Go.context,
      useRootNavigator: true,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: false,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      elevation: 0,
      builder: (_) => child,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
        boxShadow: [
          BoxShadow(
            color: AppColors.shadowBlack14,
            blurRadius: 32.r,
            offset: Offset(0, -4.h),
          ),
        ],
      ),
      child: SingleChildScrollView(
        child: SafeArea(
          top: false,
          minimum: EdgeInsets.only(bottom: 36.h),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              ExcludeSemantics(
                child: Container(
                  width: 42.w,
                  height: 4.h,
                  decoration: BoxDecoration(
                    color: AppColors.graySoft,
                    borderRadius: BorderRadius.circular(2.r),
                  ),
                ).centerWidget,
              ),
              16.szH,
              child,
            ],
          ).paddingOnly(top: 12.h, left: 20.w, right: 20.w),
        ),
      ),
    );
  }
}
