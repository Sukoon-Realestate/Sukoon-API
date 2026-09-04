import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';

class AuthScaffold extends StatelessWidget {
  const AuthScaffold({
    super.key,
    required this.child,
    this.showBackButton = true,
    this.backButton,
    this.backgroundColor = AppColors.scaffoldBackground,
    this.padding,
    this.bottomNavigationBar,
    this.isScrollable = true,
    this.resizeToAvoidBottomInset = true,
    this.backButtonAlignment = AlignmentDirectional.centerEnd,
  });

  final Widget child;
  final bool showBackButton;
  final Widget? backButton;
  final Color backgroundColor;
  final EdgeInsetsGeometry? padding;
  final Widget? bottomNavigationBar;
  final bool isScrollable;
  final bool resizeToAvoidBottomInset;
  final AlignmentGeometry backButtonAlignment;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: backgroundColor,
      bottomNavigationBar: bottomNavigationBar,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final Widget content = _buildContent().padding(
              padding ?? EdgeInsets.symmetric(horizontal: 24.w),
            );

            if (!isScrollable) {
              return content;
            }

            return SingleChildScrollView(
              keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: content,
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildContent() {
    if (!showBackButton && backButton == null) {
      return child;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        20.szH,
        Align(
          alignment: backButtonAlignment,
          child: backButton ?? const SokoonBackButton(),
        ),
        14.szH,
        child,
      ],
    );
  }
}
