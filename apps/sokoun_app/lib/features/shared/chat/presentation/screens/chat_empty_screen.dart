import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';

import '../widgets/imports.dart';

class ChatEmptyScreen extends StatelessWidget {
  const ChatEmptyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 14.h),
                decoration: const BoxDecoration(
                  border: Border(
                    bottom: BorderSide(color: AppColors.sokoonBorder),
                  ),
                ),
                child: AppText(
                  LocaleKeys.chatConversationsTitle,
                  color: AppColors.sokoonNavy,
                  fontSize: 18.sp,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const Expanded(child: ChatEmptyState()),
            ],
          ),
        ),
      ),
    );
  }
}
