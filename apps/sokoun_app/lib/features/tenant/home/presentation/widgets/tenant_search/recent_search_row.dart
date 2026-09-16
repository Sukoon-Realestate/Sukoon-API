import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';

class RecentSearchRow extends StatelessWidget {
  const RecentSearchRow({super.key, required this.search, this.onTap});

  final RecentSearchContent search;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        height: 44.h,
        decoration: const BoxDecoration(
          border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
        ),
        child: Row(
          children: [
            Icon(
              Icons.history_rounded,
              color: AppColors.sokoonMuted,
              size: 18.r,
            ),
            12.szW,
            Expanded(
              child: AppText(
                search.title,
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
                fontWeight: FontWeight.w500,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Icon(
              Icons.chevron_right_rounded,
              color: AppColors.sokoonMuted,
              size: 20.r,
            ),
          ],
        ),
      ),
    );
  }
}
