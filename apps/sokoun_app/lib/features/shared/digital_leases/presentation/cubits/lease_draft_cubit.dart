import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
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
      : perform(() async {
          final generation = AccountSession.generation;
          final read = await PremiumApiData.get<PropertyDetailsModel>(
            endpoint: ApiConstants.propertyDetails(body.propertyId),
            key: 'lease_property_${body.propertyId}',
            fromJson: PropertyDetailsModel.fromJson,
            toJson: (property) => property.toJson(),
          );
          final allowed = read.when(
            (response) =>
                generation == AccountSession.generation &&
                response.key != 'fromCache' &&
                response.data.id == body.propertyId &&
                response.data.rentalInventory == null,
            (_) => false,
          );
          if (!allowed) {
            return Error(ServerFailure(LocaleKeys.rentalUnavailableCapability));
          }
          return PremiumApiData.mutate(
            endpoint: PremiumApiConstants.leases,
            body: body.toJson(),
            fromJson: DigitalLease.fromJson,
            valid: (lease) =>
                lease.id.isNotEmpty &&
                lease.propertyId == body.propertyId &&
                lease.status.isDraft &&
                lease.revision > 0,
          );
        });
}
