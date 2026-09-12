import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';

import '../shared/chat_privacy_banner.dart';

class ChatReportSheet extends StatefulWidget {
  const ChatReportSheet({super.key});

  @override
  State<ChatReportSheet> createState() => _ChatReportSheetState();
}

class _ChatReportSheetState extends State<ChatReportSheet> {
  late final TextEditingController _detailsController;
  int _selectedReason = 0;

  List<String> get _reasons => [
    LocaleKeys.chatReportIncorrectProperty,
    LocaleKeys.chatReportOffensiveContent,
    LocaleKeys.chatReportPotentialFraud,
    LocaleKeys.chatReportPhoneInPhotos,
    LocaleKeys.chatReportUnavailableProperty,
    LocaleKeys.chatReportOtherReason,
  ];

  bool get _isOtherReason => _selectedReason == _reasons.length - 1;

  @override
  void initState() {
    super.initState();
    _detailsController = TextEditingController();
  }

  @override
  void dispose() {
    _detailsController.dispose();
    super.dispose();
  }

  void _submit() => Go.back(true);

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      heightFactor: .88,
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24.r)),
        ),
        child: SafeArea(
          top: false,
          child: Column(
            children: [
              const _ReportHeader(),
              Expanded(
                child: SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 20.h),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      for (int index = 0; index < _reasons.length; index++) ...[
                        _ReportReasonTile(
                          label: _reasons[index],
                          isSelected: _selectedReason == index,
                          onPressed: () {
                            setState(() => _selectedReason = index);
                          },
                        ),
                        if (index < _reasons.length - 1) 8.szH,
                      ],
                      if (_isOtherReason) ...[
                        12.szH,
                        TextField(
                          controller: _detailsController,
                          minLines: 3,
                          maxLines: 4,
                          textDirection: TextDirection.rtl,
                          style: TextStyle(
                            color: AppColors.sokoonNavy,
                            fontSize: 14.sp,
                            fontFamily: ConstantManager.fontFamily,
                          ),
                          decoration: InputDecoration(
                            hintText: LocaleKeys.chatReportDetailsHint,
                            hintStyle: TextStyle(
                              color: AppColors.sokoonMuted,
                              fontSize: 14.sp,
                              fontFamily: ConstantManager.fontFamily,
                            ),
                            filled: true,
                            fillColor: AppColors.white,
                            contentPadding: EdgeInsets.all(14.r),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16.r),
                              borderSide: const BorderSide(
                                color: AppColors.sokoonBorder,
                              ),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16.r),
                              borderSide: const BorderSide(
                                color: AppColors.sokoonBorder,
                              ),
                            ),
                            focusedBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(16.r),
                              borderSide: const BorderSide(
                                color: AppColors.red,
                              ),
                            ),
                          ),
                        ),
                      ],
                      16.szH,
                      ChatPrivacyBanner(text: LocaleKeys.chatReportPrivacy),
                      16.szH,
                      DefaultButton(
                        onTap: _submit,
                        title: LocaleKeys.chatSubmitReport,
                        color: AppColors.red,
                        textColor: AppColors.white,
                        borderRadius: BorderRadius.circular(16.r),
                        width: double.infinity,
                        height: 52.h,
                        fontSize: 15.sp,
                        fontWeight: FontWeight.w800,
                      ),
                      6.szH,
                      TextButton(
                        onPressed: () => Go.back(),
                        child: AppText(
                          LocaleKeys.cancel,
                          color: AppColors.sokoonGray,
                          fontSize: 14.sp,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ReportHeader extends StatelessWidget {
  const _ReportHeader();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 48.w,
          height: 6.h,
          decoration: BoxDecoration(
            color: AppColors.sokoonBorder,
            borderRadius: BorderRadius.circular(3.r),
          ),
        ),
        14.szH,
        Row(
          children: [
            SizedBox(width: 40.r),
            Expanded(
              child: AppText(
                LocaleKeys.chatReportProblemTitle,
                color: AppColors.sokoonNavy,
                fontSize: 18.sp,
                fontWeight: FontWeight.w900,
                textAlign: TextAlign.center,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
            IconButton(
              onPressed: Go.back,
              icon: Icon(
                Icons.close_rounded,
                color: AppColors.sokoonNavy,
                size: 20.r,
              ),
            ),
          ],
        ),
        AppText(
          LocaleKeys.chatReportReasonPrompt,
          color: AppColors.sokoonGray,
          fontSize: 14.sp,
          textAlign: TextAlign.center,
        ),
      ],
    ).padding(EdgeInsets.fromLTRB(20.w, 12.h, 20.w, 10.h));
  }
}

class _ReportReasonTile extends StatelessWidget {
  const _ReportReasonTile({
    required this.label,
    required this.isSelected,
    required this.onPressed,
  });

  final String label;
  final bool isSelected;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(16.r),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: EdgeInsets.symmetric(horizontal: 14.w, vertical: 13.h),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.redPale : AppColors.scaffoldBackground,
          borderRadius: BorderRadius.circular(16.r),
          border: Border.all(
            color: isSelected ? AppColors.red : AppColors.sokoonBorder,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 20.r,
              height: 20.r,
              padding: EdgeInsets.all(4.r),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: isSelected ? AppColors.red : AppColors.sokoonBorder,
                  width: 2.w,
                ),
              ),
              child: isSelected
                  ? const DecoratedBox(
                      decoration: BoxDecoration(
                        color: AppColors.red,
                        shape: BoxShape.circle,
                      ),
                    )
                  : null,
            ),
            12.szW,
            Expanded(
              child: AppText(
                label,
                color: AppColors.sokoonNavy,
                fontSize: 14.sp,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
