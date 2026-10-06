// extension to Text widget to add icon and text
import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../widgets/icon_widget.dart';
import '../widgets/pull_refresher.dart';


extension TextWithIcon on Text {
  Widget withIcon(
    IconData icon, {
    double spacing = 4.0,
    bool iconAfterText = false,
    MainAxisSize mainAxisSize = MainAxisSize.min,
    CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.center,
    MainAxisAlignment mainAxisAlignment = MainAxisAlignment.start,
    Color? iconColor,
    double? iconSize,
  }) {
    final iconWidget = IconWidget(
      icon: icon,
      color: iconColor,
      height: iconSize,
    );

    final children = iconAfterText
        ? [this, SizedBox(width: spacing.w), iconWidget]
        : [iconWidget, SizedBox(width: spacing.w), this];

    return Row(
      mainAxisSize: mainAxisSize,
      mainAxisAlignment: mainAxisAlignment,
      crossAxisAlignment: crossAxisAlignment,
      children: children,
    );
  }
}

extension Refresh on Widget{
  Widget withPullRefresher({required FutureOr<void> Function() onRefresh}){
    return PullRefresherWidget(
        onRefresh: () async => await onRefresh.call(),
        child: this
    );
  }
}

extension Visibility on Widget{
  Widget showIf({required bool Function() condition}){
    if(condition.call()){
      return this;
    }

    return SizedBox.shrink();
  }
}
