import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/res/config_imports.dart';

import 'sokoun_layout.dart';

class SokounActionFooter extends StatelessWidget {
  const SokounActionFooter({
    super.key,
    required this.child,
    this.width = SokounContentWidth.readable,
  });

  final Widget child;
  final SokounContentWidth width;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      color: AppColors.white,
      border: Border(top: BorderSide(color: AppColors.sokoonBorder)),
    ),
    child: SafeArea(
      top: false,
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: 20.w, vertical: 12.h),
        child: SokounContent(width: width, child: child),
      ),
    ),
  );
}
