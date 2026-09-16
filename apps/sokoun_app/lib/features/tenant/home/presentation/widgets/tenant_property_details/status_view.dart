import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/navigation/navigator.dart';

class TenantPropertyStatusView extends StatelessWidget {
  const TenantPropertyStatusView({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: IconButton(
            onPressed: Go.back,
            icon: Icon(Icons.arrow_back_ios_new_rounded, size: 20.r),
          ),
        ),
        Expanded(child: child),
      ],
    );
  }
}
