import 'package:sokoun_app/features/shared/premium/data/models/premium_revision_body.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import '../../data/models/premium_alert_body.dart';
import '../../data/models/premium_alert_toggle_body.dart';

class PremiumAlertSubmitCubit
    extends PremiumMutationCubit<PremiumActionReceipt> {
  PremiumAlertSubmitCubit() : super(const PremiumActionReceipt.initial());
  Future<PremiumActionReceipt?> create(PremiumAlertBody body) => !body.isValid
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.alerts,
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                (receipt.status.isActive || receipt.status.isPaused),
          ),
        );
  Future<PremiumActionReceipt?> toggle(
    String id,
    PremiumAlertToggleBody body,
  ) => id.isEmpty || body.revision <= 0 || body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.alert(id),
            method: HttpRequestType.patch,
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.subjectId == id &&
                (body.enabled
                    ? receipt.status.isActive
                    : receipt.status.isPaused),
          ),
        );
  Future<PremiumActionReceipt?> remove(String id, PremiumRevisionBody body) =>
      id.isEmpty || body.revision <= 0 || body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.alert(id),
            method: HttpRequestType.delete,
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.subjectId == id &&
                receipt.status.isCancelled,
          ),
        );
}
