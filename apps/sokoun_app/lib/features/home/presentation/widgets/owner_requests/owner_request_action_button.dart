import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/home/data/models/owner_request_content.dart';

class OwnerRequestActionButton extends StatelessWidget {
  const OwnerRequestActionButton({super.key, required this.action});

  final OwnerRequestActionContent action;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        height: 32.h,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: action.backgroundColor,
          borderRadius: BorderRadius.circular(12.r),
        ),
        child: AppText(
          action.label,
          color: action.foregroundColor,
          fontSize: 12.sp,
          fontWeight: FontWeight.w900,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
