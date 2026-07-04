import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

import '../../config/res/config_imports.dart';
import '../extensions/padding_extension.dart';
import '../extensions/sized_box_helper.dart';
import '../navigation/navigator.dart';

Future showDefaultBottomSheet({
  BuildContext? context,
  required Widget child,
  bool? enableDrag,
  Color? backgroundColor,
  bool withPadding = true,
}) {
  return showModalBottomSheet(
    enableDrag: enableDrag ?? true,
    isDismissible: false,
    useRootNavigator: false,
    isScrollControlled: true,
    context: context ?? Go.context,
    backgroundColor: backgroundColor?? Colors.white,
    barrierColor: Colors.black.withOpacity(0.8),
    builder: (context) => DefaultSheetBody(
      child: !withPadding? child :
      Padding(padding: EdgeInsets.all(12.r), child: child),
    ),
  );
}

class DefaultSheetBody extends StatelessWidget {
  final Widget child;
  const DefaultSheetBody({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          Container(
            width: 1.sw,
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
              ),
            ),
            child: Wrap(
              children: [
                Align(
                  alignment: Alignment.center,
                  child: Container(
                    width: 100.w,
                    height: 5.h,
                    decoration: BoxDecoration(
                      color: AppColors.whiteGrey,
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                ),
                AppSize.sH14.szH,
                child.paddingSymmetric(vertical: 10.h),
              ],
            ),
          ),
        ],
      ).paddingSymmetric(vertical: 5.h),
    );
  }
}
