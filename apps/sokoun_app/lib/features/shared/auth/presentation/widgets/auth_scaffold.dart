import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/extensions/padding_extension.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';

class AuthScaffold extends StatelessWidget {
  const AuthScaffold({
    super.key,
    required this.child,
    this.showBackButton = true,
    this.title,
    this.onBack,
    this.backButton,
    this.backgroundColor = AppColors.scaffoldBackground,
    this.padding,
    this.bottomNavigationBar,
    this.isScrollable = true,
    this.resizeToAvoidBottomInset = true,
  });

  final Widget child;
  final bool showBackButton;
  final String? title;
  final VoidCallback? onBack;
  final Widget? backButton;
  final Color backgroundColor;
  final EdgeInsetsGeometry? padding;
  final Widget? bottomNavigationBar;
  final bool isScrollable;
  final bool resizeToAvoidBottomInset;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: title,
      showBackButton: showBackButton,
      onBack: onBack,
      backButton: backButton,
      backgroundColor: backgroundColor,
      contentWidth: SokounContentWidth.form,
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      bottomBar: bottomNavigationBar,
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            final Widget content = child.padding(
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
}
