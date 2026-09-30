import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/available_places_cubit.dart';
import 'package:sokoun_app/shared_widgets/sokoun_reveal.dart';

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
        style: AppTextStyles.regular12.copyWith(
          color: AppColors.sokoonMuted,
          fontSize: 12.sp,
          height: 1.45,
        ),
        textAlign: TextAlign.start,
      );
    }

    return StatusBuilder<
      AvailablePlacesCubit,
      AvailablePlacesModel
    >.withShimmer(
      initialDataForShimmer: const AvailablePlacesModel.initial(),
      onRetry: context.read<AvailablePlacesCubit>().retry,
      errorType: ErrorType.defaultView,
      builder: (data) => data.places.isEmpty
          ? const SearchAvailablePlacesEmptyState()
          : SokounReveal(
              delay: const Duration(milliseconds: 60),
              child: SuggestedAreasGrid(
                places: data.places,
                selectedArea: selectedArea,
                onAreaSelected: onAreaSelected,
              ),
            ),
    );
  }
}
