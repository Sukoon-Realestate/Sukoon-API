import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import '../../data/models/rent_invoice.dart';

class RentInvoiceCubit extends AsyncCubit<RentInvoice> {
  RentInvoiceCubit() : super(const RentInvoice.initial());
  bool _isCached = true;
  bool get isCached => _isCached;
  Future<void> load(String id) async {
    if (id.isEmpty || isClosed || isLoading) return;
    await executeAsyncWithBaseModel(
      operation: () => PremiumApiData.get(
        endpoint: PremiumApiConstants.invoice(id),
        key: premiumCacheKey('rent_invoice', [id]),
        fromJson: RentInvoice.fromJson,
        valid: (invoice) => invoice.id == id,
        toJson: (model) => model.toJson(),
      ),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
