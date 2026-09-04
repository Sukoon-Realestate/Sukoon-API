import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../widgets/auth_scaffold.dart';
import '../widgets/kyc/kyc_status_summary_card.dart';

class KycPendingScreen extends StatelessWidget {
  const KycPendingScreen({
    super.key,
    this.fullName = 'سارة أحمد خالد',
    this.maskedNationalId = '29•••••••••12',
    this.submittedAt,
    this.expectedReviewTime,
    this.onBackHome,
  });

  final String fullName;
  final String maskedNationalId;
  final String? submittedAt;
  final String? expectedReviewTime;
  final VoidCallback? onBackHome;

  @override
  Widget build(BuildContext context) {
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
              color: AppColors.amber,
              fontSize: 12.sp,
              fontWeight: FontWeight.w600,
            ),
          ).centerWidget,
          14.szH,
          AppText(
            LocaleKeys.kycPendingTitle,
            color: AppColors.sokoonNavy,
            fontSize: 24.sp,
            fontWeight: FontWeight.w900,
            textAlign: TextAlign.center,
          ),
          8.szH,
          AppText(
            LocaleKeys.kycPendingDescription,
            color: AppColors.sokoonGray,
            fontSize: 14.sp,
            fontWeight: FontWeight.w400,
            textAlign: TextAlign.center,
            height: 1.45,
          ),
          24.szH,
          KycStatusSummaryCard(
            rows: [
              KycStatusSummaryRow(label: LocaleKeys.name, value: fullName),
              KycStatusSummaryRow(
                label: LocaleKeys.cardNumber,
                value: maskedNationalId,
              ),
              KycStatusSummaryRow(
                label: LocaleKeys.submittedAt,
                value: submittedAt ?? LocaleKeys.today941Am,
              ),
              KycStatusSummaryRow(
                label: LocaleKeys.expected,
                value: expectedReviewTime ?? LocaleKeys.within24Hours,
              ),
            ],
          ),
          24.szH,
          DefaultButton(
            onTap: onBackHome,
            title: LocaleKeys.returnHome,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
    );
  }
}
