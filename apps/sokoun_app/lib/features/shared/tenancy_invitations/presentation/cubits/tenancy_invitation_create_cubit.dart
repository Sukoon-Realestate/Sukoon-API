import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import 'package:sokoun_app/features/shared/rental_offers/data/models/rental_selection.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_details_model.dart';
import 'package:uuid/uuid.dart';
import '../../data/models/create_tenancy_invitation_body.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitation_capabilities.dart';
import '../../data/tenancy_invitations_data.dart';

class TenancyInvitationCreateCubit
    extends PremiumMutationCubit<TenancyInvitation> {
  TenancyInvitationCreateCubit() : super(const TenancyInvitation.initial());
  List<Object?>? _subject;
  String _requestKey = '';
  final int _generation = AccountSession.generation;

  Future<TenancyInvitation?> create({
    required String propertyId,
    required String tenantId,
    RentalSelection? selection,
  }) async {
    if (isClosed ||
        isLoading ||
        _generation != AccountSession.generation ||
        !checkVerification()) {
      return null;
    }
    if (!TenancyInvitationCapabilities.current.enabled) {
      setError(errorMessage: LocaleKeys.tenancyInvitationsUnavailable);
      return null;
    }
    final subject = [
      propertyId,
      tenantId,
      selection?.offerId,
      selection?.offerRevision,
    ];
    if (_subject == null || !_sameSubject(subject)) {
      _subject = subject;
      _requestKey = const Uuid().v4();
    }
    final body = CreateTenancyInvitationBody(
      propertyId: propertyId,
      tenantId: tenantId,
      offerId: selection?.offerId ?? '',
      expectedOfferRevision: selection?.offerRevision ?? 0,
      requestKey: _requestKey,
    );
    if (!body.isValid || tenantId == TenancyInvitationsData.accountId) {
      return null;
    }
    return perform(() async {
      final property = await PremiumApiData.get<PropertyDetailsModel>(
        endpoint: ApiConstants.propertyDetails(propertyId),
        key: premiumCacheKey('lease_property', [propertyId]),
        fromJson: PropertyDetailsModel.fromJson,
        toJson: (item) => item.toJson(),
        valid: (item) => item.id == propertyId,
      );
      final failure = property.tryGetError();
      if (failure != null) return Error(failure);
      if (_generation != AccountSession.generation) {
        return Error(ServerFailure(LocaleKeys.paidInvalidResponse));
      }
      final allowed = property.when((response) {
        if (response.key == 'fromCache') return false;
        final inventory = response.data.rentalInventory;
        if (inventory == null) return selection == null;
        final offer = inventory.offerById(body.offerId);
        if (!inventory.isSupported ||
            offer == null ||
            !offer.isAvailable ||
            selection == null) {
          return false;
        }
        final fresh = RentalSelection.fromOffer(
          propertyId: propertyId,
          inventory: inventory,
          offer: offer,
        );
        return fresh.canIdentify && fresh.sameTermsAs(selection);
      }, (_) => false);
      if (!allowed) {
        return Error(
          ServerFailure(LocaleKeys.tenancyInvitationAccommodationChanged),
        );
      }
      final result = await TenancyInvitationsData.create(body);
      return result.when(
        (response) =>
            selection == null ||
                response.data.rentalSelection?.sameTermsAs(selection) == true
            ? Success(response)
            : Error(ServerFailure(LocaleKeys.paidInvalidResponse)),
        Error.new,
      );
    });
  }

  bool _sameSubject(List<Object?> next) {
    for (int index = 0; index < next.length; index++) {
      if (_subject![index] != next[index]) return false;
    }
    return true;
  }
}
