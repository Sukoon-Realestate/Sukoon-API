import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:sokoun_app/shared_widgets/sokoun_action_footer.dart';
import 'package:sokoun_app/shared_widgets/sokoun_motion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/first_validation_error_form.dart';

import 'add_property_primary_button.dart';

class AddPropertyStepShell extends StatefulWidget {
  const AddPropertyStepShell({
    super.key,
    required this.children,
    required this.primaryLabel,
    required this.activeSegments,
    required this.validationFields,
    this.onPrimaryTap,
    this.progressSubtitle,
    this.segmentCount = 4,
    this.secondaryLabel,
    this.onSecondaryTap,
  });

  final List<Widget> children;
  final FirstValidationErrorFieldsBuilder validationFields;
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
  final ValueNotifier<bool> _hasAttempted = ValueNotifier(false);

  @override
  void dispose() {
    _hasAttempted.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<bool>(
      valueListenable: _hasAttempted,
      builder: (context, hasAttempted, _) => FirstValidationErrorForm(
        validationFields: widget.validationFields,
        onValid: () => widget.onPrimaryTap?.call(),
        autovalidateMode: hasAttempted
            ? AutovalidateMode.always
            : AutovalidateMode.disabled,
        scrollDuration: SokounMotion.duration(context, milliseconds: 280),
        builder: (context, submit) => Column(
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
                    onTap: widget.onPrimaryTap == null
                        ? null
                        : () {
                            _hasAttempted.value = true;
                            submit();
                          },
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
      ),
    );
  }
}
