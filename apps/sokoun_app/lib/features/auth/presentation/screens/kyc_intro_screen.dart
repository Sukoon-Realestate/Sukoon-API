import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../widgets/kyc/kyc_flow_header.dart';
import '../widgets/kyc/kyc_privacy_card.dart';
import '../widgets/kyc/kyc_progress_bar.dart';
import '../widgets/kyc/kyc_requirement_tile.dart';

class KycIntroScreen extends StatelessWidget {
  const KycIntroScreen({super.key, this.onBack, this.onUploadDocuments});

  final VoidCallback? onBack;
  final VoidCallback? onUploadDocuments;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: Column(
          children: [
            KycFlowHeader(
              title: LocaleKeys.identityVerification,
              onBack: onBack,
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: EdgeInsets.all(16.w),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const KycProgressBar(currentStep: 1),
                    24.szH,
                    Container(
                      width: 72.r,
                      height: 72.r,
                      decoration: BoxDecoration(
                        color: AppColors.tealAlpha09,
                        borderRadius: BorderRadius.circular(22.r),
                      ),
                      child: Icon(
                        Icons.verified_user_outlined,
                        color: AppColors.sokoonTeal,
                        size: 36.r,
                      ),
                    ).centerWidget,
                    14.szH,
                    AppText(
                      LocaleKeys.verifyIdentityAndStart,
                      color: AppColors.sokoonNavy,
                      fontSize: 20.sp,
                      fontWeight: FontWeight.w900,
                      textAlign: TextAlign.center,
                    ),
                    8.szH,
                    AppText(
                      LocaleKeys.kycIntroDescription,
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                      fontWeight: FontWeight.w400,
                      textAlign: TextAlign.center,
                      height: 1.45,
                    ),
                    26.szH,
                    AppText(
                      LocaleKeys.requiredDocuments,
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                      fontWeight: FontWeight.w800,
                    ),
                    10.szH,
                    KycRequirementTile(
                      icon: Icons.credit_card_rounded,
                      title: LocaleKeys.nationalIdFrontBack,
                      isHighlighted: true,
                      isComplete: true,
                    ),
                    8.szH,
                    KycRequirementTile(
                      icon: Icons.photo_camera_outlined,
                      title: LocaleKeys.clearSelfie,
                    ),
                    14.szH,
                    KycPrivacyCard(
                      title: LocaleKeys.kycPrivacyIntroTitle,
                      subtitle: LocaleKeys.internalReviewOnly,
                    ),
                    24.szH,
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Container(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
          decoration: const BoxDecoration(
            color: AppColors.white,
            border: Border(top: BorderSide(color: AppColors.grayPale)),
          ),
          child: DefaultButton(
            onTap: onUploadDocuments,
            title: LocaleKeys.uploadDocuments,
            color: AppColors.sokoonTeal,
            textColor: AppColors.white,
            borderRadius: BorderRadius.circular(14.r),
            height: 52.h,
            width: double.infinity,
            fontSize: 16.sp,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}
