import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/presentation/screens/kyc_intro_screen.dart';
import 'package:sokoun_app/features/chat/data/models/chat_content.dart';

class ChatRestrictedScreen extends StatelessWidget {
  const ChatRestrictedScreen({super.key, required this.conversation});

  final ConversationContent conversation;

  void _openVerification() => Go.to(const KycIntroScreen());

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          bottom: false,
          child: Column(
            children: [
              _RestrictedHeader(conversation: conversation),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.symmetric(
                    horizontal: 28.w,
                    vertical: 28.h,
                  ),
                  child: Column(
                    children: [
                      Container(
                        width: 80.r,
                        height: 80.r,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          color: AppColors.orangePale,
                          borderRadius: BorderRadius.circular(24.r),
                        ),
                        child: Icon(
                          Icons.lock_outline_rounded,
                          color: AppColors.amber,
                          size: 34.r,
                        ),
                      ),
                      18.szH,
                      AppText(
                        LocaleKeys.chatRestrictedTitle,
                        color: AppColors.sokoonNavy,
                        fontSize: 18.sp,
                        fontWeight: FontWeight.w900,
                        textAlign: TextAlign.center,
                        maxLines: 2,
                      ),
                      8.szH,
                      AppText(
                        LocaleKeys.chatRestrictedDescription,
                        color: AppColors.sokoonGray,
                        fontSize: 14.sp,
                        height: 1.55,
                        textAlign: TextAlign.center,
                        maxLines: 3,
                      ),
                      18.szH,
                      _VerificationWarning(onVerifyPressed: _openVerification),
                      20.szH,
                      DefaultButton(
                        key: const ValueKey('chat-start-kyc'),
                        onTap: _openVerification,
                        title: LocaleKeys.chatStartKyc,
                        color: AppColors.sokoonTeal,
                        textColor: AppColors.white,
                        borderRadius: BorderRadius.circular(16.r),
                        width: double.infinity,
                        height: 52.h,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w800,
                      ),
                      12.szH,
                      DefaultButton(
                        onTap: _openVerification,
                        title: LocaleKeys.chatLearnMoreVerification,
                        color: AppColors.white,
                        textColor: AppColors.sokoonNavy,
                        borderColor: AppColors.sokoonBorder,
                        borderRadius: BorderRadius.circular(16.r),
                        width: double.infinity,
                        height: 52.h,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w800,
                      ),
                    ],
                  ),
                ),
              ),
              _DisabledComposer(),
            ],
          ),
        ),
      ),
    );
  }
}

class _RestrictedHeader extends StatelessWidget {
  const _RestrictedHeader({required this.conversation});

  final ConversationContent conversation;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.fromLTRB(14.w, 8.h, 20.w, 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(bottom: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: Row(
        children: [
          IconButton(
            key: const ValueKey('chat-restricted-back'),
            onPressed: () => Go.back(),
            icon: Icon(
              Icons.arrow_back_ios_new_rounded,
              color: AppColors.sokoonNavy,
              size: 18.r,
            ),
          ),
          Container(
            width: 38.r,
            height: 38.r,
            alignment: Alignment.center,
            decoration: const BoxDecoration(
              color: AppColors.grayPale,
              shape: BoxShape.circle,
            ),
            child: Icon(
              Icons.person_outline_rounded,
              color: AppColors.sokoonMuted,
              size: 18.r,
            ),
          ),
          10.szW,
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AppText(
                  conversation.name,
                  color: AppColors.sokoonNavy,
                  fontSize: 14.sp,
                  fontWeight: FontWeight.w900,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                2.szH,
                AppText(
                  conversation.property,
                  color: AppColors.sokoonGray,
                  fontSize: 11.sp,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _VerificationWarning extends StatelessWidget {
  const _VerificationWarning({required this.onVerifyPressed});

  final VoidCallback onVerifyPressed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: BoxDecoration(
        color: AppColors.orangePale,
        borderRadius: BorderRadius.circular(16.r),
      ),
      child: Row(
        children: [
          Icon(Icons.warning_amber_rounded, color: AppColors.amber, size: 16.r),
          8.szW,
          Expanded(
            child: AppText(
              LocaleKeys.chatVerifiedOnlyBanner,
              color: AppColors.brown,
              fontSize: 12.sp,
              fontWeight: FontWeight.w500,
              maxLines: 2,
            ),
          ),
          TextButton(
            onPressed: onVerifyPressed,
            style: TextButton.styleFrom(
              minimumSize: Size.zero,
              padding: EdgeInsets.symmetric(horizontal: 4.w, vertical: 2.h),
              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
            child: AppText(
              LocaleKeys.chatVerifyNow,
              color: AppColors.sokoonTeal,
              fontSize: 12.sp,
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}

class _DisabledComposer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
      decoration: const BoxDecoration(
        color: AppColors.white,
        border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
      ),
      child: SafeArea(
        top: false,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 12.h),
          decoration: BoxDecoration(
            color: AppColors.scaffoldBackground,
            borderRadius: BorderRadius.circular(16.r),
          ),
          child: Row(
            children: [
              Icon(
                Icons.lock_outline_rounded,
                color: AppColors.sokoonMuted,
                size: 16.r,
              ),
              8.szW,
              Expanded(
                child: AppText(
                  LocaleKeys.chatTypingDisabled,
                  color: AppColors.sokoonMuted,
                  fontSize: 13.sp,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
