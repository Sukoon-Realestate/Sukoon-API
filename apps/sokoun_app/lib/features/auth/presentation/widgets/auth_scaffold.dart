import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/shared_widgets/sokoon_back_button.dart';

class AuthScaffold extends StatelessWidget {
  const AuthScaffold({
    super.key,
    required this.child,
    this.showBackButton = true,
    this.backButton,
    this.onBack,
    this.backgroundColor = AppColors.scaffoldBackground,
    this.padding,
    this.resizeToAvoidBottomInset = true,
    this.backButtonAlignment = AlignmentDirectional.centerEnd,
  });

  final Widget child;
  final bool showBackButton;
  final Widget? backButton;
  final VoidCallback? onBack;
  final Color backgroundColor;
  final EdgeInsetsGeometry? padding;
  final bool resizeToAvoidBottomInset;
  final AlignmentGeometry backButtonAlignment;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: backgroundColor,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Padding(
                  padding: padding ?? EdgeInsets.symmetric(horizontal: 24.w),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (showBackButton || backButton != null) ...[
                        20.szH,
                        Align(
                          alignment: backButtonAlignment,
                          child: backButton ?? SokoonBackButton(onTap: onBack),
                        ),
                        14.szH,
                      ],
                      child,
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
