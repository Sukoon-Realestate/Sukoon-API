import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/owner/home/data/enums/property_price_period.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/enums/rental_scope.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/rental_offer_capabilities.dart';
import '../../data/models/property_search_model.dart';
import '../../data/rental_home_section_data.dart';

class RentalHomeSectionCubit extends AsyncCubit<PropertySearchResponseModel> {
  RentalHomeSectionCubit({
    required this.scope,
    required this.period,
    this.capabilities = RentalOfferCapabilities.configured,
  }) : super(const PropertySearchResponseModel.initial());

  final RentalScope scope;
  final PropertyPricePeriod period;
  final RentalOfferCapabilities capabilities;

  Future<void> load() async {
    if (isClosed || isLoading) return;
    if (!capabilities.canSearch) {
      updateErrorMessage(LocaleKeys.rentalScopeFilterUnavailable);
      setError();
      return;
    }
    await executeAsyncWithBaseModel(
      operation: () => baseCrudUseCase.call(
        RentalHomeSectionData.request(
          scope: scope,
          period: period,
          capabilities: capabilities,
        ),
      ),
      withInternetInterceptor: true,
    );
  }
}
