import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/shared_widgets/back_button.dart';
import 'sokoun_layout.dart';

class AppScaffold extends StatelessWidget {
  const AppScaffold({
    super.key,
    required this.body,
    this.title,
    this.titleWidget,
    this.actions = const [],
    this.bottomBar,
    this.showBackButton = true,
    this.backButton,
    this.backgroundColor = AppColors.scaffoldBackground,
    this.resizeToAvoidBottomInset,
    this.contentWidth = SokounContentWidth.readable,
  });

  final Widget body;
  final String? title;
  final Widget? titleWidget;
  final List<Widget> actions;
  final Widget? bottomBar;
  final bool showBackButton;
  final Widget? backButton;
  final Color backgroundColor;
  final bool? resizeToAvoidBottomInset;
  final SokounContentWidth contentWidth;

  bool get _hasAppBar =>
      showBackButton ||
      backButton != null ||
      title != null ||
      titleWidget != null ||
      actions.isNotEmpty;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: backgroundColor,
      appBar: _hasAppBar ? _buildAppBar() : null,
      body: SokounContent(width: contentWidth, child: body),
      bottomNavigationBar: bottomBar == null
          ? null
          : Padding(
              padding: EdgeInsets.only(
                bottom: resizeToAvoidBottomInset == false
                    ? 0
                    : MediaQuery.viewInsetsOf(context).bottom,
              ),
              child: SokounContent(width: contentWidth, child: bottomBar!),
            ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      automaticallyImplyLeading: false,
      backgroundColor: backgroundColor,
      surfaceTintColor: AppColors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: true,
      leadingWidth: 60.w,
      leading: showBackButton || backButton != null
          ? Center(child: backButton ?? const SokoonBackButton())
          : null,
      title: titleWidget ?? _buildTitle(),
      actions: actions,
    );
  }

  Widget? _buildTitle() {
    final title = this.title;
    if (title == null) {
      return null;
    }

    return AppText(
      title,
      style: AppTextStyles.extraBold.copyWith(
        color: AppColors.sokoonNavy,
        fontSize: 16.sp,
      ),
      overflow: TextOverflow.ellipsis,
      maxLines: 1,
      textAlign: TextAlign.center,
    );
  }
}
