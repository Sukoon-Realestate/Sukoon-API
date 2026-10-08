import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/models/rent_checkout_body.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';
import 'package:sokoun_app/features/shared/premium/data/feature_service_capabilities.dart';

class RentCheckoutCubit extends PremiumMutationCubit<PremiumActionReceipt> {
  RentCheckoutCubit({this.capabilities = FeatureServiceCapabilities.configured})
    : super(const PremiumActionReceipt.initial());
  final FeatureServiceCapabilities capabilities;
  Future<PremiumActionReceipt?> checkout(RentCheckoutBody body) =>
      !capabilities.rentCheckout ||
          body.invoiceId.isEmpty ||
          body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.rentCheckout(body.invoiceId),
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.status.isPending &&
                receipt.subjectId == body.invoiceId &&
                receipt.amount.isKnown &&
                receipt.amount.amountMinor! > 0 &&
                PremiumHostedData.httpsUri(receipt.hostedUrl) != null &&
                receipt.expiresAt != null &&
                receipt.expiresAt!.isAfter(DateTime.now()),
          ),
        );
}
