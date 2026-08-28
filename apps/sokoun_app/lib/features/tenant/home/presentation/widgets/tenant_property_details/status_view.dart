import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';

class TenantPropertyStatusView extends StatelessWidget {
  const TenantPropertyStatusView({
    super.key,
    required this.onBackPressed,
    required this.child,
  });

  final VoidCallback onBackPressed;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Align(
          alignment: Alignment.centerLeft,
          child: IconButton(
            onPressed: onBackPressed,
            icon: Icon(Icons.arrow_back_ios_new_rounded, size: 20.r),
          ),
        ),
        Expanded(child: child),
      ],
    );
  }
}
