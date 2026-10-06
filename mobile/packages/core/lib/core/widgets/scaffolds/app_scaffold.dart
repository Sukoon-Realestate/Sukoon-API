import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../../config/res/config_imports.dart';
import '../../extensions/context_extension.dart';
import '../../extensions/padding_extension.dart';
import '../../navigation/navigator.dart';
import '../app_text.dart';

class AppScaffold extends StatelessWidget {
  final String? appBarTitle;
  final Widget? customTitle;
  final Widget body;
  final Color? scaffoldBackgroundColor;
  final Widget? bottomBar;
  final PreferredSizeWidget? bottomWidget;
  final double? appBarHeight;
  final List<Widget>? actions;
  final bool isScrollable;
  final bool? resizeToAvoidBottomInset;
  final FutureOr<void> Function()? onBack;
  // final FutureOr<void> Function(BuildContext context)? onRefresh;

  const AppScaffold({
    super.key,
    required this.body,
    this.appBarTitle,
    this.customTitle,
    this.scaffoldBackgroundColor,
    this.bottomBar,
    this.bottomWidget,
    this.appBarHeight,
    this.actions,
    this.onBack,
    this.isScrollable = true,
    this.resizeToAvoidBottomInset,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: resizeToAvoidBottomInset,
      backgroundColor: scaffoldBackgroundColor ?? Colors.white,
      appBar: PreferredSize(
        preferredSize: Size(context.width, appBarHeight ?? 60),
        child: AppBar(
          actionsPadding: EdgeInsets.all(10.r),
          backgroundColor: context.appColor(
            AppColors.whiteGreyColor,
            surface: true,
          ),
          centerTitle: true,
          title:
              customTitle ??
              AppText(
                appBarTitle ?? '',
                fontWeight: FontWeight.bold,
                fontSize: 16.sp,
                color: Colors.black,
              ),
          leading: ModalRoute.of(context)!.canPop
              ? AppBackButton(onBack: onBack)
              : null,
          bottom: bottomWidget,
          actions: actions
              ?.map((e) => SizedBox.square(dimension: 30.sp, child: e))
              .toList(),
        ),
      ),
      body: isScrollable
          ? SingleChildScrollView(
              child: Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16.r),
                ),
                child: body.defaultScreenPadding(),
              ),
            )
          : body.defaultScreenPadding(),
      bottomNavigationBar: bottomBar,
    );
  }
}

class AppBackButton extends StatelessWidget {
  final FutureOr<void> Function()? onBack;
  const AppBackButton({super.key, this.onBack});
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 50,
      height: 50,
      child: FittedBox(
        child: Container(
          decoration: const BoxDecoration(
            color: Colors.white,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            onPressed: () async {
              onBack?.call();
              Go.back();
            },
            icon: const Icon(
              Icons.arrow_back_ios_sharp,
              color: Colors.black,
              size: 14,
            ),
          ),
        ).paddingAll(12.r),
      ),
    );
  }
}
