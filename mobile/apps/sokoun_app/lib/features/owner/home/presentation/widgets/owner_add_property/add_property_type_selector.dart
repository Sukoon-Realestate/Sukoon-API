import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_types_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_search/search_options_empty_state.dart';

import '../../../data/models/owner_add_property_content.dart';
import 'add_property_chip.dart';

class AddPropertyTypeSelector extends StatefulWidget {
  const AddPropertyTypeSelector({
    super.key,
    required this.selectedValue,
    required this.onSelected,
  });

  final String selectedValue;
  final ValueChanged<PropertyTypeModel> onSelected;

  @override
  State<AddPropertyTypeSelector> createState() =>
      _AddPropertyTypeSelectorState();
}

class _AddPropertyTypeSelectorState extends State<AddPropertyTypeSelector> {
  late final PropertyTypesCubit _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = PropertyTypesCubit();
    _cubit.getPropertyTypes();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider<PropertyTypesCubit>.value(
    value: _cubit,
    child: StatusBuilder<PropertyTypesCubit, PropertyTypesModel>.withShimmer(
      initialDataForShimmer: const PropertyTypesModel.initial(),
      onRetry: _cubit.getPropertyTypes,
      shimmerBuilder: (_) => const AddPropertyChip(
        chip: AddPropertyChipContent(label: '••••••••'),
      ),
      builder: (data) {
        final List<PropertyTypeModel> types = data.results
            .where((type) => type.slug.isNotEmpty && type.name.isNotEmpty)
            .toList(growable: false);
        if (types.isEmpty) return const SearchPropertyTypesEmptyState();
        return Wrap(
          spacing: 8.w,
          runSpacing: 8.h,
          children: [
            for (final type in types)
              AddPropertyChip(
                chip: AddPropertyChipContent(
                  label: type.name,
                  isSelected: type.slug == widget.selectedValue,
                ),
                onTap: () => widget.onSelected(type),
              ),
          ],
        );
      },
    ),
  );
}
