import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

class ChatMentionedPropertyRow extends StatelessWidget {
  const ChatMentionedPropertyRow({super.key, required this.property});

  final String property;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(vertical: 12.h),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        spacing: 12.w,
        children: [
          Container(
            width: 36.r,
            height: 36.r,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.grayBluePale,
              borderRadius: BorderRadius.circular(12.r),
            ),
            child: Icon(
              Icons.apartment_rounded,
              color: AppColors.blueGrayLight,
              size: 16.r,
            ),
          ),
          Expanded(
            child: AppText(
              property,
              style: AppTextStyles.regular14.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
                height: 1.45,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}
