import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/home/data/models/home_page_model.dart';
import 'package:sokoun_app/features/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/features/home/presentation/screens/tenant_property_details_screen.dart';
import 'tenant_property_card.dart';

class SuggestedPropertiesSection extends StatelessWidget {
  const SuggestedPropertiesSection({super.key});

  @override
  Widget build(BuildContext context) {
    return StatusBuilder<HomePageCubit, HomePageModel>(
      builder: (properties) => Column(
        spacing: 12.h,
        children: properties.results.map(
              (property) => GestureDetector(
            onTap: () => Go.to(
              TenantPropertyDetailsScreen(propertyId: property.id),
            ),
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
        ).toList()
      ),
    );
  }
}
