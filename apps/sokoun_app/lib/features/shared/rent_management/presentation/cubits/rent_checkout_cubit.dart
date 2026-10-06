import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/models/rent_checkout_body.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_hosted_data.dart';

class RentCheckoutCubit extends PremiumMutationCubit<PremiumActionReceipt> {
  RentCheckoutCubit() : super(const PremiumActionReceipt.initial());
  Future<PremiumActionReceipt?> checkout(RentCheckoutBody body) =>
      body.invoiceId.isEmpty || body.requestKey.isEmpty
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
