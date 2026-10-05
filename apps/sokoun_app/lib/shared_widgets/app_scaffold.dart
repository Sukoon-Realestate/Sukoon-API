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
    this.onBack,
    this.isBackEnabled = true,
    this.toolbarHeight,
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
  final VoidCallback? onBack;
  final bool isBackEnabled;
  final double? toolbarHeight;
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
      backgroundColor: context.appColor(backgroundColor, surface: true),
      appBar: _hasAppBar ? _buildAppBar(context) : null,
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

  PreferredSizeWidget _buildAppBar(BuildContext context) {
    return AppBar(
      automaticallyImplyLeading: false,
      backgroundColor: context.appColor(backgroundColor, surface: true),
      surfaceTintColor: AppColors.transparent,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: true,
      toolbarHeight: toolbarHeight,
      leadingWidth: 60.w,
      leading: showBackButton || backButton != null
          ? Center(
              child:
                  backButton ??
                  SokoonBackButton(onTap: onBack, enabled: isBackEnabled),
            )
          : null,
      title: titleWidget ?? _buildTitle(context),
      actions: actions,
      actionsPadding: EdgeInsetsDirectional.only(end: 8.w),
    );
  }

  Widget? _buildTitle(BuildContext context) {
    final title = this.title;
    if (title == null) {
      return null;
    }

    return AppText(
      title,
      style: AppTextStyles.extraBold.copyWith(
        color: context.appColor(AppColors.sokoonNavy),
        fontSize: 16.sp,
      ),
      overflow: TextOverflow.ellipsis,
      maxLines: 1,
      textAlign: TextAlign.center,
    );
  }
}
