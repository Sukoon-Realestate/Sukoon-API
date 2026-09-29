import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_search_content.dart';

class RecentSearchRow extends StatelessWidget {
  const RecentSearchRow({
    super.key,
    required this.search,
    this.onTap,
    this.onRemove,
  });

  final RecentSearchContent search;
  final VoidCallback? onTap;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      behavior: HitTestBehavior.opaque,
      child: Container(
        constraints: BoxConstraints(minHeight: 48.h),
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
            if (onRemove != null)
              IconButton(
                tooltip: '${LocaleKeys.removeRecentSearch}: ${search.title}',
                onPressed: onRemove,
                icon: Icon(
                  Icons.close_rounded,
                  color: AppColors.sokoonGray,
                  size: 18.r,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
