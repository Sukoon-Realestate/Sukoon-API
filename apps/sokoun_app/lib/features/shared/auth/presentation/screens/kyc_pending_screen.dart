import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/kyc/kyc_status_summary_card.dart';

class KycPendingScreen extends StatelessWidget {
  const KycPendingScreen({
    super.key,
    this.fullName,
    this.submittedAt,
    this.expectedReviewTime,
    this.existingAccount = false,
  });

  final String? fullName;
  final String? submittedAt;
  final String? expectedReviewTime;
  final bool existingAccount;

  @override
  Widget build(BuildContext context) {
    final List<KycStatusSummaryRow> summaryRows = [
      if (_hasValue(fullName))
        KycStatusSummaryRow(label: LocaleKeys.name, value: fullName!.trim()),
      if (_hasValue(submittedAt))
        KycStatusSummaryRow(
          label: LocaleKeys.submittedAt,
          value: submittedAt!.trim(),
        ),
      if (_hasValue(expectedReviewTime))
        KycStatusSummaryRow(
          label: LocaleKeys.expected,
          value: expectedReviewTime!.trim(),
        ),
    ];

    return AuthScaffold(
      padding: EdgeInsets.symmetric(horizontal: 32.w, vertical: 24.h),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: 96.r,
            height: 96.r,
            decoration: const BoxDecoration(
              color: AppColors.orangePale,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.schedule_rounded,
              color: AppColors.amber,
              size: 44.r,
            ),
          ),
          14.szH,
          Container(
            padding: EdgeInsets.symmetric(horizontal: 10.w, vertical: 4.h),
            decoration: BoxDecoration(
              color: AppColors.orangePale,
              borderRadius: BorderRadius.circular(999.r),
            ),
            child: AppText(
              LocaleKeys.kycPendingBadge,
              style: AppTextStyles.semiBold.copyWith(
                color: AppColors.amber,
                fontSize: 12.sp,
              ),
            ),
          ).centerWidget,
          14.szH,
          AppText(
            LocaleKeys.kycPendingTitle,
            style: AppTextStyles.bold.copyWith(
              color: AppColors.sokoonNavy,
              fontSize: 24.sp,
            ),
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            LocaleKeys.kycPendingDescription,
            style: AppTextStyles.regular14.copyWith(
              color: AppColors.sokoonGray,
              fontSize: 14.sp,
              height: 1.45,
            ),
            textAlign: TextAlign.center,
          ),
          24.szH,
          if (summaryRows.isNotEmpty) ...[
            KycStatusSummaryCard(rows: summaryRows),
            24.szH,
          ],
          DefaultButton(
            onTap: () =>
                existingAccount ? Go.backToInitial() : Go.offAll(LoginScreen()),
            title: LocaleKeys.ok,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            textStyle: AppTextStyles.bold16.copyWith(
              fontSize: 16.sp,
              height: 1.45,
            ),
          ),
        ],
      ),
    );
  }

  bool _hasValue(String? value) => value?.trim().isNotEmpty ?? false;
}
