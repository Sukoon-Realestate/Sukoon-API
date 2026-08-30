import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/available_places_cubit.dart';

import 'search_options_empty_state.dart';
import 'suggested_areas_grid.dart';

class AvailablePlacesSection extends StatelessWidget {
  const AvailablePlacesSection({
    super.key,
    required this.requestToTryAgainWhenError,
    required this.selectedArea,
    required this.onAreaSelected,
  });

  final Future<void>? requestToTryAgainWhenError;
  final String? selectedArea;
  final ValueChanged<AvailablePlaceModel> onAreaSelected;

  @override
  Widget build(BuildContext context) {
    final Future<void>? request = requestToTryAgainWhenError;
    if (request == null) {
      return AppText(
        LocaleKeys.tenantSearchSelectPropertyType,
        color: AppColors.sokoonMuted,
        fontSize: 12.sp,
        textAlign: TextAlign.start,
      );
    }

    return StatusBuilder<
      AvailablePlacesCubit,
      AvailablePlacesModel
    >.withShimmer(
      initialDataForShimmer: const AvailablePlacesModel.initial(),
      requestToTryAgainWhenError: request,
      errorType: ErrorType.defaultView,
      builder: (data) => data.places.isEmpty
          ? const SearchAvailablePlacesEmptyState()
          : SuggestedAreasGrid(
              places: data.places,
              selectedArea: selectedArea,
              onAreaSelected: onAreaSelected,
            ),
    );
  }
}
