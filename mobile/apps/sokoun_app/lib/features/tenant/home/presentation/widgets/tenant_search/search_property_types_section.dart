import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_types_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/property_types_cubit.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

import 'search_category_chips.dart';
import 'search_options_empty_state.dart';

class SearchPropertyTypesSection extends StatelessWidget {
  const SearchPropertyTypesSection({
    super.key,
    required this.requestToTryAgainWhenError,
    required this.selectedCategory,
    required this.onCategorySelected,
  });

  final Future<void> requestToTryAgainWhenError;
  final String selectedCategory;
  final ValueChanged<PropertyTypeModel> onCategorySelected;

  @override
  Widget build(BuildContext context) {
    return StatusBuilder<PropertyTypesCubit, PropertyTypesModel>.withShimmer(
      initialDataForShimmer: const PropertyTypesModel.initial(),
      onRetry: context.read<PropertyTypesCubit>().getPropertyTypes,
      errorType: ErrorType.defaultView,
      builder: (data) => data.results.isEmpty
          ? const SearchPropertyTypesEmptyState()
          : SokounReveal(
              child: SearchCategoryChips(
                propertyTypes: data.results,
                selectedCategory: selectedCategory,
                onCategorySelected: onCategorySelected,
              ),
            ),
    );
  }
}
