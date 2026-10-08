import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_revision_body.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';

class LeaseActionCubit extends PremiumMutationCubit<PremiumActionReceipt> {
  LeaseActionCubit({this.capabilities = FeatureServiceCapabilities.configured})
    : super(const PremiumActionReceipt.initial());
  final FeatureServiceCapabilities capabilities;
  Future<PremiumActionReceipt?> signing(String id, PremiumRevisionBody body) =>
      !capabilities.leaseSigning ||
          id.isEmpty ||
          body.revision <= 0 ||
          body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.signing(id),
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.status.isPending &&
                receipt.subjectId == id &&
                PremiumHostedData.httpsUri(receipt.hostedUrl) != null &&
                receipt.expiresAt != null &&
                receipt.expiresAt!.isAfter(DateTime.now()),
          ),
        );
  Future<PremiumActionReceipt?> cancel(String id, PremiumRevisionBody body) =>
      id.isEmpty || body.revision <= 0 || body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.cancelLease(id),
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.subjectId == id &&
                receipt.status.isCancelled,
          ),
        );
}
