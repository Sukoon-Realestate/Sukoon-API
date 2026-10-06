import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:sokoun_app/features/tenant/home/data/models/available_places_model.dart';

import 'suggested_area_card.dart';

class SuggestedAreasGrid extends StatelessWidget {
  const SuggestedAreasGrid({
    super.key,
    required this.places,
    this.selectedArea,
    this.onAreaSelected,
  });

  final List<AvailablePlaceModel> places;
  final String? selectedArea;
  final ValueChanged<AvailablePlaceModel>? onAreaSelected;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 3,
        childAspectRatio: .82,
        crossAxisSpacing: 10.w,
        mainAxisSpacing: 10.h,
      ),
      itemCount: places.length,
      itemBuilder: (context, index) {
        final AvailablePlaceModel place = places[index];
        return SuggestedAreaCard(
          place: place,
          styleIndex: index,
          isSelected: place.searchQuery == selectedArea,
          onTap: onAreaSelected == null ? null : () => onAreaSelected!(place),
        );
      },
    );
  }
}
