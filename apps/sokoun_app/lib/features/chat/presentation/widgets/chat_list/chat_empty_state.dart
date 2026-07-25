import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

class ChatEmptyState extends StatelessWidget {
  const ChatEmptyState({super.key, required this.onExplorePressed});

  final VoidCallback onExplorePressed;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 40.w, vertical: 32.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 88.r,
              height: 88.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.mintLight,
                borderRadius: BorderRadius.circular(28.r),
              ),
              child: Icon(
                Icons.chat_bubble_outline_rounded,
                color: AppColors.sokoonTeal,
                size: 40.r,
              ),
            ),
            24.szH,
            AppText(
              LocaleKeys.chatEmptyTitle,
              color: AppColors.sokoonNavy,
              fontSize: 20.sp,
              fontWeight: FontWeight.w900,
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            10.szH,
            AppText(
              LocaleKeys.chatEmptyDescription,
              color: AppColors.sokoonGray,
              fontSize: 14.sp,
              height: 1.7,
              textAlign: TextAlign.center,
              maxLines: 4,
              overflow: TextOverflow.ellipsis,
            ),
            30.szH,
            DefaultButton(
              onTap: onExplorePressed,
              title: LocaleKeys.chatExploreProperties,
              color: AppColors.sokoonTeal,
              textColor: AppColors.white,
              borderRadius: BorderRadius.circular(16.r),
              width: double.infinity,
              height: 52.h,
              fontSize: 15.sp,
              fontWeight: FontWeight.w800,
            ),
          ],
        ),
      ),
    );
  }
}
