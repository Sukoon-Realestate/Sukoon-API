import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_filter_options_model.dart';

class FilterChipWrap extends StatelessWidget {
  const FilterChipWrap({
    super.key,
    required this.options,
    required this.selectedValues,
    required this.onSelected,
  });

  final List<TenantFilterOption> options;
  final Set<String> selectedValues;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.end,
      spacing: 8.w,
      runSpacing: 8.h,
      children: [
        for (final TenantFilterOption option in options)
          SokounSelectionChip(
            label: option.label,
            selected: selectedValues.contains(option.selectionValue),
            onPressed: () => onSelected(option.selectionValue),
          ),
      ],
    );
  }
}
