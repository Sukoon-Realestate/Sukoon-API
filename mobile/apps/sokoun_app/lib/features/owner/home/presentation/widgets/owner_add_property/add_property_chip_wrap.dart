import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

import 'add_property_chip.dart';

class AddPropertyChipWrap extends StatelessWidget {
  const AddPropertyChipWrap({
    super.key,
    required this.chips,
    this.onChipTap,
    this.showCheck = true,
  });

  final List<AddPropertyChipContent> chips;
  final ValueChanged<AddPropertyChipContent>? onChipTap;
  final bool showCheck;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.end,
      spacing: 8.w,
      runSpacing: 8.h,
      children: [
        for (final chip in chips)
          AddPropertyChip(
            chip: chip,
            showCheck: showCheck,
            onTap: onChipTap == null ? null : () => onChipTap!(chip),
          ),
      ],
    );
  }
}
