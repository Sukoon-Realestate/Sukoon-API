import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

import '../cubits/workspace_cubit.dart';
import '../cubits/account_cubit.dart';
import '../../data/account_access.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';

class VerificationRequiredContent extends StatelessWidget {
  const VerificationRequiredContent({super.key});

  static bool allowAction() {
    if (AccountAccess.isVerified) return true;
    unawaited(openVerification());
    return false;
  }

  static Future<void> openVerification() async {
    final int generation = AccountSession.generation;
    final AppWorkspace workspace = injector.isRegistered<WorkspaceCubit>()
        ? WorkspaceCubit.instance.state
        : AppWorkspace.tenant;
    await Go.to(ProfileVerificationScreen(workspace: workspace));
    if (generation != AccountSession.generation ||
        !injector.isRegistered<UserCubit>() ||
        !UserCubit.instance.isUserLoggedIn) {
      return;
    }
    final AccountCubit cubit = AccountCubit();
    try {
      await cubit.getAccount();
    } finally {
      await cubit.close();
    }
  }

  @override
  Widget build(BuildContext context) => Center(
    child: SingleChildScrollView(
      padding: EdgeInsets.all(24.r),
      child: SokounContent(
        width: SokounContentWidth.form,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Icon(
              Icons.lock_outline_rounded,
              size: 48.r,
              color: context.appColor(AppColors.sokoonTeal),
            ),
            16.szH,
            AppText(
              LocaleKeys.accountVerificationRequiredTitle,
              style: AppTextStyles.bold.copyWith(
                fontSize: 18.sp,
                color: context.appColor(AppColors.sokoonNavy),
              ),
              textAlign: TextAlign.center,
            ),
            12.szH,
            AppText(
              LocaleKeys.accountVerificationRequired,
              style: AppTextStyles.regular14.copyWith(
                color: context.appColor(AppColors.sokoonGray),
                height: 1.5,
              ),
              textAlign: TextAlign.center,
            ),
            24.szH,
            DefaultButton(
              title: LocaleKeys.chatVerifyNow,
              onTap: openVerification,
            ),
          ],
        ),
      ),
    ),
  );
}
