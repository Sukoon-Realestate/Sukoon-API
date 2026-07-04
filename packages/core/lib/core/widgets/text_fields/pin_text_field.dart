import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:pinput/pinput.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/context_extension.dart';
import '../../extensions/text_style_extensions.dart';
import '../../helpers/validators.dart';
import '../custom_widget_validator.dart';

class CustomPinTextField extends StatelessWidget {
  final ValueChanged<String>? onCompleted;
  final TextEditingController controller;
  const CustomPinTextField(
      {super.key, required this.controller, this.onCompleted});

  @override
  Widget build(BuildContext context) {
    final defaultPinTheme = PinTheme(
      width: AppSize.sH60,
      height: AppSize.sH60,
      textStyle: const TextStyle().setMainTextColor.s14.medium,
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(context.width.r),
        border: Border.all(color: AppColors.border),
      ),
    );
    final focusedPinTheme = defaultPinTheme.copyDecorationWith(
      border: Border.all(color: AppColors.primary),
    );
    final errorPinTheme = defaultPinTheme.copyDecorationWith(
      border: Border.all(color: AppColors.error),
    );
    return Directionality(
      textDirection: TextDirection.ltr,
      child: CustomWidgetValidator(
        validator: Validators.validateEmpty,
        builder: (state) {
          return Pinput(
            length: ConstantManager.pinCodeFieldsCount,
            controller: controller,
            keyboardType: TextInputType.number,
            autofocus: true,
            forceErrorState: state.hasError,
            focusedPinTheme: focusedPinTheme,
            defaultPinTheme: defaultPinTheme,
            errorPinTheme: errorPinTheme,
            onCompleted: onCompleted,
            closeKeyboardWhenCompleted: true,
            errorTextStyle: const TextStyle().setErrorColor.s10.regular,
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            pinAnimationType: PinAnimationType.scale,
            inputFormatters: [FilteringTextInputFormatter.digitsOnly],
            textInputAction: TextInputAction.done,
            onChanged: (value) => state.didChange(value),
            validator: (value) => Validators.validateEmpty(value),
          );
        },
      ),
    );
  }
}
