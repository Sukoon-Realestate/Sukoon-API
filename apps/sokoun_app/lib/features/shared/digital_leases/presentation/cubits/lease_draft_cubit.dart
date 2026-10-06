import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/lease_rules.dart';
import '../../data/models/digital_lease.dart';
import '../../data/models/lease_draft_body.dart';

class LeaseDraftCubit extends PremiumMutationCubit<DigitalLease> {
  LeaseDraftCubit() : super(const DigitalLease.initial());
  Future<DigitalLease?> create(LeaseDraftBody body) => !LeaseRules.valid(body)
      ? Future.value()
      : perform(
          () => PremiumApiData.mutate(
            endpoint: PremiumApiConstants.leases,
            body: body.toJson(),
            fromJson: DigitalLease.fromJson,
            valid: (lease) =>
                lease.id.isNotEmpty &&
                lease.propertyId == body.propertyId &&
                lease.status.isDraft &&
                lease.revision > 0,
          ),
        );
}
