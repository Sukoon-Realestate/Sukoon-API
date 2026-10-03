import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';

import 'add_property_primary_button.dart';

class AddPropertyStepShell extends StatefulWidget {
  const AddPropertyStepShell({
    super.key,
    required this.children,
    required this.primaryLabel,
    required this.activeSegments,
    this.onPrimaryTap,
    this.progressSubtitle,
    this.segmentCount = 4,
    this.secondaryLabel,
    this.onSecondaryTap,
  });

  final List<Widget> children;
  final String primaryLabel;
  final VoidCallback? onPrimaryTap;
  final int activeSegments;
  final String? progressSubtitle;
  final int segmentCount;
  final String? secondaryLabel;
  final VoidCallback? onSecondaryTap;

  @override
  State<AddPropertyStepShell> createState() => _AddPropertyStepShellState();
}

class _AddPropertyStepShellState extends State<AddPropertyStepShell> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();

  bool _hasAttempted = false;

  void _continue() {
    setState(() => _hasAttempted = true);
    FocusManager.instance.primaryFocus?.unfocus();
    final Set<FormFieldState<Object?>> invalid = _formKey.currentState!
        .validateGranularly();
    if (invalid.isEmpty) {
      widget.onPrimaryTap?.call();
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      Scrollable.ensureVisible(
        invalid.first.context,
        alignment: .12,
        duration: SokounMotion.duration(context, milliseconds: 280),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      autovalidateMode: _hasAttempted
          ? AutovalidateMode.always
          : AutovalidateMode.disabled,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
            decoration: const BoxDecoration(
              color: AppColors.white,
              border: Border(bottom: BorderSide(color: AppColors.grayPale)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              spacing: 8.h,
              children: [
                Row(
                  spacing: 6.w,
                  children: [
                    for (int index = 0; index < widget.segmentCount; index++)
                      Expanded(
                        child: AnimatedContainer(
                          duration: SokounMotion.duration(context),
                          height: 4.h,
                          decoration: BoxDecoration(
                            color: index < widget.activeSegments
                                ? AppColors.sokoonTeal
                                : AppColors.grayPale,
                            borderRadius: BorderRadius.circular(999.r),
                          ),
                        ),
                      ),
                  ],
                ),
                AppText(
                  LocaleKeys.propertyRequiredFieldsHint,
                  style: AppTextStyles.regular12.copyWith(
                    color: AppColors.sokoonGray,
                  ),
                ),
                if (widget.progressSubtitle != null)
                  AppText(
                    widget.progressSubtitle!,
                    style: AppTextStyles.regular11.copyWith(
                      color: AppColors.sokoonGray,
                      fontSize: 12.sp,
                      height: 1.45,
                    ),
                    textAlign: TextAlign.start,
                  ),
              ],
            ),
          ),
          Expanded(
            child: SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(16.w, 16.w, 16.w, 16.w + 24.h),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                spacing: 12.h,
                children: widget.children,
              ),
            ),
          ),
          SokounActionFooter(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              spacing: 10.h,
              children: [
                AddPropertyPrimaryButton(
                  label: widget.primaryLabel,
                  onTap: widget.onPrimaryTap == null ? null : _continue,
                ),
                if (widget.secondaryLabel != null)
                  AddPropertyPrimaryButton(
                    label: widget.secondaryLabel!,
                    isOutline: true,
                    onTap: widget.onSecondaryTap,
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
