import 'dart:async';

import '../base_crud/code/domain/base_domain_imports.dart';
import '../base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import '../network/api_endpoints.dart';
import 'models/payment_brand.dart';

class PaymentBrandsCubit extends AsyncCubit<List<PaymentBrand>>{
  PaymentBrandsCubit() : super([]);

  Future<void> get()async{
    await executeAsyncWithBaseModel(
        operation: () async => await baseCrudUseCase.call(
            CrudBaseParmas(
              api: ApiConstants.getPaymentBrands,
              httpRequestType: HttpRequestType.get,
              mapper: (json) => (json as List).map((e) => PaymentBrand.fromJson(e)).toList()
            )
        ),
    );
  }
}