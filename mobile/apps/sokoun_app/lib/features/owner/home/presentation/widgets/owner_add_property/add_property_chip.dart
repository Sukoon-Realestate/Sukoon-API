import 'package:flutter/material.dart';
import 'package:sokoun_app/shared_widgets/sokoun_selection_chip.dart';
import 'package:sokoun_app/features/owner/home/data/models/owner_add_property_content.dart';

class AddPropertyChip extends StatelessWidget {
  const AddPropertyChip({
    super.key,
    required this.chip,
    this.showCheck = true,
    this.onTap,
  });

  final AddPropertyChipContent chip;
  final bool showCheck;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => SokounSelectionChip(
    label: chip.label,
    selected: chip.isSelected,
    showCheck: showCheck,
    onPressed: onTap,
  );
}
