import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/home/data/models/tenant_search_content.dart';
import 'package:sokoun_app/features/home/presentation/cubits/property_types_cubit.dart';

import 'search_chip.dart';

class SearchCategoryChips extends StatefulWidget {
  const SearchCategoryChips({
    super.key,
    required this.selectedCategory,
    this.onCategorySelected,
  });

  final String selectedCategory;
  final ValueChanged<PropertyTypeModel?>? onCategorySelected;

  @override
  State<SearchCategoryChips> createState() => _SearchCategoryChipsState();
}

class _SearchCategoryChipsState extends State<SearchCategoryChips> {
  late final PropertyTypesCubit _propertyTypesCubit;
  late final Future<void> _propertyTypesRequest;

  @override
  void initState() {
    super.initState();
    _propertyTypesCubit = PropertyTypesCubit();
    _propertyTypesRequest = _propertyTypesCubit.getPropertyTypes();
  }

  @override
  void dispose() {
    _propertyTypesCubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocProvider.value(
      value: _propertyTypesCubit,
      child: StatusBuilder<PropertyTypesCubit, PropertyTypesModel>.withShimmer(
        initialDataForShimmer: const PropertyTypesModel.initial(),
        requestToTryAgainWhenError: _propertyTypesRequest,
        errorType: ErrorType.defaultView,
        builder: (data) => _PropertyTypeChips(
          propertyTypes: data.results,
          selectedCategory: widget.selectedCategory,
          onCategorySelected: widget.onCategorySelected,
        ),
      ),
    );
  }
}

class _PropertyTypeChips extends StatelessWidget {
  const _PropertyTypeChips({
    required this.propertyTypes,
    required this.selectedCategory,
    this.onCategorySelected,
  });

  final List<PropertyTypeModel> propertyTypes;
  final String selectedCategory;
  final ValueChanged<PropertyTypeModel?>? onCategorySelected;

  @override
  Widget build(BuildContext context) {
    final List<SearchCategoryContent> categories = [
      // SearchCategoryContent(
      //   label: LocaleKeys.tenantSearchAll,
      //   isSelected: selectedCategory.isEmpty,
      // ),
      ...propertyTypes.map(
        (propertyType) => SearchCategoryContent(
          label: propertyType.name,
          isSelected: propertyType.slug == selectedCategory,
        ),
      ),
    ];

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        textDirection: TextDirection.ltr,
        children: [
          for (int index = 0; index < categories.length; index++) ...[
            SearchChip(
              category: categories[index],
              onTap: onCategorySelected == null
                  ? null
                  : () => onCategorySelected!(
                      index == 0 ? null : propertyTypes[index - 1],
                    ),
            ),
            if (index < categories.length - 1) 8.szW,
          ],
        ],
      ),
    );
  }
}
