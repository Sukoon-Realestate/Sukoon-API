import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'models/rent_overview.dart';

abstract final class RentOverviewData {
  static Future<Result<BaseModel<RentOverview>, Failure>> get(
    AppWorkspace workspace,
  ) async {
    final result = await PremiumApiData.get(
      endpoint: PremiumApiConstants.invoices,
      key: premiumCacheKey('rent_overview', [
        workspace.name,
        'due,overdue',
        'due_date',
        1,
        1,
      ]),
      query: {
        'workspace': workspace.name,
        'status': 'due,overdue',
        'ordering': 'due_date',
        'page': 1,
        'page_size': 1,
      },
      fromJson: RentOverview.fromJson,
      toJson: (model) => model.toJson(),
    );
    return result.when(
      (response) => response.data.isValid
          ? Success(response)
          : Error(ServerFailure(LocaleKeys.paidInvalidResponse)),
      Error.new,
    );
  }
}
