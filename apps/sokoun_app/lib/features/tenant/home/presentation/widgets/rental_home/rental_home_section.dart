import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/extensions/sized_box_helper.dart';
import 'package:melos_core/core/helpers/status_builder.dart';
import 'package:melos_core/core/helpers/text_style_manager.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import '../../../data/models/property_search_model.dart';
import '../../../data/rental_home_section_data.dart';
import '../../cubits/rental_home_section_cubit.dart';
import '../../screens/tenant_search_results_screen.dart';
import 'rental_home_section_preview.dart';

class RentalHomeSection extends StatefulWidget {
  const RentalHomeSection({
    super.key,
    required this.scope,
    required this.period,
    this.capabilities = RentalOfferCapabilities.configured,
  });

  final RentalScope scope;
  final PropertyPricePeriod period;
  final RentalOfferCapabilities capabilities;

  @override
  State<RentalHomeSection> createState() => _RentalHomeSectionState();
}

class _RentalHomeSectionState extends State<RentalHomeSection> {
  late final RentalHomeSectionCubit _cubit;
  late final Future<void> _request;

  @override
  void initState() {
    super.initState();
    _cubit = RentalHomeSectionCubit(
      scope: widget.scope,
      period: widget.period,
      capabilities: widget.capabilities,
    );
    _request = _cubit.load();
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  String get _title => switch (widget.scope) {
    RentalScope.entireProperty => LocaleKeys.rentalHomeEntireProperties,
    RentalScope.room => LocaleKeys.rentalHomeRooms,
    RentalScope.roomGroup => LocaleKeys.rentalHomeRoomGroups,
    RentalScope.bed => LocaleKeys.rentalHomeBeds,
  };

  @override
  Widget build(BuildContext context) {
    final filters = RentalHomeSectionData.filters(widget.scope, widget.period);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          children: [
            AppText(_title, style: AppTextStyles.bold16),
            TextButton(
              onPressed: () =>
                  Go.to(TenantSearchResultsScreen(initialFilters: filters)),
              child: AppText(LocaleKeys.tenantHomeViewAll),
            ),
          ],
        ),
        BlocProvider.value(
          value: _cubit,
          child: FutureBuilder<void>(
            future: _request,
            builder: (context, _) =>
                StatusBuilder<
                  RentalHomeSectionCubit,
                  PropertySearchResponseModel
                >.withShimmer(
                  initialDataForShimmer:
                      const PropertySearchResponseModel.initial(),
                  onRetry: _cubit.load,
                  shimmerBuilder: (_) => Container(
                    height: 160,
                    color: Theme.of(
                      context,
                    ).colorScheme.surfaceContainerHighest,
                  ),
                  builder: (data) =>
                      RentalHomeSectionPreview(data: data, filters: filters),
                ),
          ),
        ),
        16.szH,
      ],
    );
  }
}
