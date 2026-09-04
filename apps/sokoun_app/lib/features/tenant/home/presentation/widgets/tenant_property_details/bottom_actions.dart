import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/tenant_property_content.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

class TenantPropertyBottomActions extends StatelessWidget {
  const TenantPropertyBottomActions({
    super.key,
    required this.property,
    required this.isSaved,
    required this.onSavedPressed,
  });

  final TenantPropertyDetailsContent property;
  final bool isSaved;
  final VoidCallback onSavedPressed;

  void _openBookVisit() {
    Go.to(
      BookVisitScreen(
        property: VisitPropertyContent.fromPropertyDetails(property),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 18.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.grayPale)),
      ),
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          Expanded(
            child: GestureDetector(
              key: const ValueKey('tenant-property-details-book-visit'),
              onTap: _openBookVisit,
              behavior: HitTestBehavior.opaque,
              child: Container(
                height: 48.h,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: AppColors.sokoonTeal,
                  borderRadius: BorderRadius.circular(14.r),
                ),
                child: AppText(
                  LocaleKeys.tenantVisitBookTitle,
                  color: AppColors.white,
                  fontSize: 15.sp,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ),
          10.szW,
          GestureDetector(
            key: const ValueKey('tenant-property-details-bottom-save'),
            onTap: onSavedPressed,
            behavior: HitTestBehavior.opaque,
            child: Container(
              width: 48.r,
              height: 48.r,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: AppColors.grayBackground,
                borderRadius: BorderRadius.circular(14.r),
              ),
              child: Icon(
                isSaved
                    ? Icons.bookmark_rounded
                    : Icons.bookmark_border_rounded,
                color: AppColors.sokoonTeal,
                size: 22.r,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
