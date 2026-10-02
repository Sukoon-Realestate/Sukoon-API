import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/helpers/user_type/user_enum.dart';
import 'package:melos_core/core/helpers/user_type/user_type_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_property_flow_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_search_screen.dart';
import 'package:melos_core/generated/assets.dart';

class ChatEmptyState extends StatelessWidget {
  const ChatEmptyState({super.key});

  @override
  Widget build(BuildContext context) {
    final bool reduceMotion = MediaQuery.of(context).disableAnimations;
    return Semantics(
      label: LocaleKeys.chatEmptyTitle,
      child: SingleChildScrollView(
        padding: EdgeInsets.symmetric(horizontal: 40.w, vertical: 32.h),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ExcludeSemantics(
              child: Assets.lottie.noData.lottie(
                width: 132.r,
                height: 112.r,
                fit: BoxFit.contain,
                package: 'melos_core',
                animate: !reduceMotion,
                repeat: false,
              ),
            ),
            24.szH,
            AppText(
              LocaleKeys.chatEmptyTitle,
              style: AppTextStyles.bold.copyWith(
                color: AppColors.sokoonNavy,
                fontSize: 20.sp,
              ),
              textAlign: TextAlign.center,
              maxLines: 2,
            ),
            10.szH,
            ...[
              AppText(
                LocaleKeys.chatEmptyDescription,
                style: AppTextStyles.regular14.copyWith(
                  color: AppColors.sokoonGray,
                  fontSize: 14.sp,
                  height: 1.7,
                ),
                textAlign: TextAlign.center,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
              ),
              30.szH,
              DefaultButton(
                onTap: () => Go.to(
                  UserTypeHelper.instance.currentUserType.isTenant
                      ? const TenantSearchScreen()
                      : const OwnerPropertyFlowScreen(),
                ),
                title: UserTypeHelper.instance.currentUserType.isTenant
                    ? LocaleKeys.chatExploreProperties
                    : LocaleKeys.ownerAddPropertyTitle,
                color: AppColors.sokoonTeal,
                textColor: AppColors.white,
                borderRadius: BorderRadius.circular(16.r),
                width: double.infinity,
                height: 52.h,
                textStyle: AppTextStyles.extraBold15.copyWith(
                  fontSize: 15.sp,
                  height: 1.45,
                ),
              ),
            ],
          ],
        ),
      ),
    ).centerWidget;
  }
}
