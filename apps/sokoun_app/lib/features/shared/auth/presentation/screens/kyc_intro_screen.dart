import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/align_helper.dart';
import 'package:melos_core/core/extensions/object.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/app_loading_button.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../widgets/auth_scaffold.dart';
import 'kyc_upload_documents_screen.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import '../widgets/kyc/kyc_privacy_card.dart';
import '../widgets/kyc/kyc_progress_bar.dart';
import '../widgets/kyc/kyc_requirement_tile.dart';

class KycIntroScreen extends StatelessWidget {
  const KycIntroScreen({
    super.key,
    this.onBack,
    this.onUploadDocuments,
    this.onSkip,
  });

  final VoidCallback? onBack;
  final VoidCallback? onUploadDocuments;
  final Future<void> Function()? onSkip;

  @override
  Widget build(BuildContext context) {
    return AuthScaffold(
      showBackButton: true,
      isScrollable: false,
      padding: EdgeInsets.zero,
      bottomNavigationBar: SafeArea(
        child: Container(
          padding: EdgeInsets.fromLTRB(16.w, 12.h, 16.w, 16.h),
          decoration: const BoxDecoration(
            color: AppColors.white,
            border: Border(top: BorderSide(color: AppColors.grayPale)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DefaultButton(
                onTap:
                    onUploadDocuments ??
                    () => WorkspaceNavigation.open(
                      detail: () => Go.to(
                        const KycUploadDocumentsScreen(existingAccount: true),
                      ),
                    ),
                title: LocaleKeys.uploadDocuments,
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
              10.szH,
              if (!onSkip.isNull)
                AppLoadingButton(
                  asyncCall: (c) async => await onSkip!(),
                  title: LocaleKeys.skip,
                  buttonColor: AppColors.whiteGreyColor,
                  textColor: AppColors.sokoonTeal,
                  borderRadius: 14.r,
                  height: 48.h,
                  width: double.infinity,
                  textStyle: AppTextStyles.bold15.copyWith(
                    fontSize: 15.sp,
                    height: 1.45,
                  ),
                ),
            ],
          ),
        ),
      ),
      onBack: onBack,
      title: LocaleKeys.identityVerification,
      child: Column(
        children: [
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
                    style: AppTextStyles.bold.copyWith(
                      color: AppColors.sokoonNavy,
                      fontSize: 20.sp,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  8.szH,
                  AppText(
                    LocaleKeys.kycIntroDescription,
                    style: AppTextStyles.regular13.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 13.sp,
                      height: 1.45,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  26.szH,
                  AppText(
                    LocaleKeys.requiredDocuments,
                    style: AppTextStyles.extraBold.copyWith(
                      color: AppColors.sokoonNavy,
                      fontSize: 14.sp,
                    ),
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
    );
  }
}
