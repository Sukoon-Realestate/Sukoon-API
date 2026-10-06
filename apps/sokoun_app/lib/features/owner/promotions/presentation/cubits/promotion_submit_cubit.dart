import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/models/premium_action_receipt.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/models/promotion_body.dart';

class PromotionSubmitCubit extends PremiumMutationCubit<PremiumActionReceipt> {
  PromotionSubmitCubit() : super(const PremiumActionReceipt.initial());
  Future<PremiumActionReceipt?> submit(PromotionBody body) =>
      body.propertyId.isEmpty ||
          body.optionId.isEmpty ||
          body.requestKey.isEmpty
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.campaigns,
            body: body.toJson(),
            fromJson: PremiumActionReceipt.fromJson,
            valid: (receipt) =>
                receipt.isValid &&
                receipt.subjectId == body.propertyId &&
                (receipt.status.isActive || receipt.status.isPending),
          ),
        );
}
