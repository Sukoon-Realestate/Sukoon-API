import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';
import 'tenant_property_card.dart';

class SuggestedPropertiesSection extends StatelessWidget {
  const SuggestedPropertiesSection({
    required this.requestToTryAgainWhenError,
    required this.onPropertyPressed,
    super.key,
  });

  final Future<void> requestToTryAgainWhenError;
  final ValueChanged<String> onPropertyPressed;

  @override
  Widget build(BuildContext context) {
    return StatusBuilder<HomePageCubit, HomePageModel>.withShimmer(
      initialDataForShimmer: HomePageModel.initial(),
      requestToTryAgainWhenError: requestToTryAgainWhenError,
      builder: (properties) => Column(
        spacing: 12.h,
        children: properties.results
            .map(
              (property) => GestureDetector(
                onTap: () => onPropertyPressed(property.id),
                behavior: HitTestBehavior.opaque,
                child: TenantPropertyCard(
                  title: property.title,
                  rating: property.formattedRate,
                  area: property.formattedArea,
                  price: property.formattedPrice,
                  icon: property.propertyIcon,
                  imageUrl: property.mainImage,
                ),
              ),
            )
            .toList(),
      ),
    );
  }
}
