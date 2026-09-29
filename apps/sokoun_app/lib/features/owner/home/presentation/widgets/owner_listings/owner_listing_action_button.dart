import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_listing_content.dart';

class OwnerListingActionButton extends StatelessWidget {
  const OwnerListingActionButton({super.key, required this.action});

  final OwnerListingActionContent action;

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
          fontWeight: FontWeight.w700,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          textAlign: TextAlign.center,
        ),
      ),
    );
  }
}
