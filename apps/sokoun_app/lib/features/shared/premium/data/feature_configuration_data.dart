import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'premium_api_constants.dart';
import 'premium_api_data.dart';
import 'premium_json.dart';
import 'models/feature_configuration.dart';

abstract final class FeatureConfigurationData {
  static Future<Result<BaseModel<FeatureConfiguration>, Failure>> get(
    AppWorkspace workspace, {
    required String language,
  }) => PremiumApiData.get(
    endpoint: PremiumApiConstants.configuration,
    key: premiumCacheKey('configuration', [workspace.name, language]),
    query: {'workspace': workspace.name, 'lang': language},
    fromJson: FeatureConfiguration.fromJson,
    toJson: (model) => model.toJson(),
  );
}
