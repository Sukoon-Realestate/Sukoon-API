import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';

class TenantVisitBanner extends StatelessWidget {
  const TenantVisitBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      child: GestureDetector(
        onTap: () {
          if (WorkspaceNavigation.isAuthenticated) {
            Go.to(const TenantVisitsScreen(useRequestEndpoint: false));
          } else {
            WorkspaceNavigation.open(
              workspace: AppWorkspace.tenant,
              tab: WorkspaceTab.visits,
              showLoginSheet: true,
            );
          }
        },
        behavior: HitTestBehavior.opaque,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 13.h),
          decoration: BoxDecoration(
            color: AppColors.mintLight,
            borderRadius: BorderRadius.circular(16.r),
            border: Border.all(color: AppColors.tealAlpha19),
          ),
          child: Row(
            children: [
              Container(
                width: 34.r,
                height: 34.r,
                decoration: const BoxDecoration(
                  color: AppColors.whiteAlpha60,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.calendar_today_outlined,
                  color: AppColors.sokoonTeal,
                  size: 17.r,
                ),
              ),
              12.szW,
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  spacing: 3.h,
                  children: [
                    AppText(
                      LocaleKeys.tenantVisitBannerTitle,
                      style: AppTextStyles.bold14.copyWith(
                        color: AppColors.sokoonTeal,
                        fontSize: 14.sp,
                        height: 1.45,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    AppText(
                      LocaleKeys.tenantVisitBannerProperty,
                      style: AppTextStyles.medium12.copyWith(
                        color: AppColors.sokoonTeal,
                        fontSize: 12.sp,
                        height: 1.45,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.chevron_right_rounded, color: AppColors.sokoonTeal),
            ],
          ),
        ),
      ),
    );
  }
}
