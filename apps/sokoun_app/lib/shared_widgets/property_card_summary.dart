import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';

/// Shared reading order for discovery, search and saved property cards.
class PropertyCardSummary extends StatelessWidget {
  const PropertyCardSummary({
    super.key,
    required this.title,
    required this.price,
    required this.metadata,
    this.location = '',
    this.tags,
    this.action,
  });

  final String title;
  final String location;
  final String price;
  final Widget metadata;
  final Widget? tags;
  final Widget? action;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    spacing: 8.h,
    children: [
      AppText(
        title,
        style: AppTextStyles.bold16.copyWith(
          color: context.appColor(AppColors.sokoonNavy),
        ),
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      if (location.trim().isNotEmpty)
        Row(
          spacing: 4.w,
          children: [
            Icon(
              Icons.location_on_outlined,
              color: context.appColor(AppColors.sokoonGray),
              size: 16.r,
            ),
            Expanded(
              child: AppText(
                location,
                style: AppTextStyles.regular13.copyWith(
                  color: context.appColor(AppColors.sokoonGray),
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      metadata,
      if (tags != null) tags!,
      Wrap(
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        spacing: 12.w,
        runSpacing: 8.h,
        children: [
          AppText(
            price,
            style: AppTextStyles.bold.copyWith(
              color: context.appColor(AppColors.sokoonTeal),
              fontSize: 18.sp,
            ),
          ),
          if (action != null) action!,
        ],
      ),
    ],
  );
}
