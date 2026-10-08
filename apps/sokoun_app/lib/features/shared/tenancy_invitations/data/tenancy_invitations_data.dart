import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart' show injector;
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:pagify/helpers/data_and_pagination_data.dart';
import 'package:sokoun_app/features/main_view/data/account_access.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_constants.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_api_data.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';

import 'enums/tenancy_invitation_status.dart';
import 'models/create_tenancy_invitation_body.dart';
import 'models/tenancy_invitation.dart';
import 'models/respond_tenancy_invitation_body.dart';
import 'tenancy_invitation_capabilities.dart';

/// Agreed routes in TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md.
abstract final class TenancyInvitationApi {
  static const collection = '${PremiumApiConstants.prefix}tenancy-invitations/';
  static String detail(String id) => '$collection${Uri.encodeComponent(id)}/';
  static String respond(String id) => '${detail(id)}respond/';
}

abstract final class TenancyInvitationsData {
  static String get accountId => injector.isRegistered<UserCubit>()
      ? injector<UserCubit>().user.id
      : UserModel.currentUser?.id ?? '';

  static String cacheKey(AppWorkspace workspace, {String propertyId = ''}) =>
      AccountSession.cacheKey(
        premiumCacheKey('tenancy_invitations', [workspace.name, propertyId]),
      );

  static String detailCacheKey(String id, AppWorkspace workspace) =>
      premiumCacheKey('tenancy_invitation', [workspace.name, id]);

  static void _requireAccess() {
    final failure = _accessFailure();
    if (failure != null) throw StateError(failure.message);
  }

  static Failure? _accessFailure() {
    if (!AccountAccess.isVerified) {
      return ServerFailure(LocaleKeys.accountVerificationRequired);
    }
    if (!TenancyInvitationCapabilities.current.enabled) {
      return ServerFailure(LocaleKeys.tenancyInvitationsUnavailable);
    }
    return accountId.isEmpty
        ? ServerFailure(LocaleKeys.paidInvalidResponse)
        : null;
  }

  static Future<(List<TenancyInvitation>, PaginationData)> getPage({
    required int page,
    required AppWorkspace workspace,
    String propertyId = '',
  }) async {
    _requireAccess();
    final generation = AccountSession.generation;
    final actor = accountId;
    final result = await PremiumApiData.page(
      endpoint: TenancyInvitationApi.collection,
      page: page,
      query: {
        'workspace': workspace.name,
        if (propertyId.isNotEmpty) 'property_id': propertyId,
      },
      fromJson: TenancyInvitation.fromJson,
    );
    _requireAccess();
    if (generation != AccountSession.generation ||
        actor != accountId ||
        result.$1.any(
          (item) =>
              !item.hasValidIdentity ||
              !item.belongsTo(actor, workspace) ||
              (propertyId.isNotEmpty && item.propertyId != propertyId),
        ) ||
        result.$1.map((item) => item.id).toSet().length != result.$1.length) {
      throw StateError(LocaleKeys.paidInvalidResponse);
    }
    return result;
  }

  static Future<Result<BaseModel<TenancyInvitation>, Failure>> get({
    required String id,
    required AppWorkspace workspace,
  }) async {
    final failure = _accessFailure();
    if (failure != null) return Error(failure);
    final actor = accountId;
    return PremiumApiData.get(
      endpoint: TenancyInvitationApi.detail(id),
      key: detailCacheKey(id, workspace),
      fromJson: TenancyInvitation.fromJson,
      toJson: (item) => item.toJson(),
      valid: (item) =>
          item.id == id &&
          item.hasValidIdentity &&
          actor == accountId &&
          item.belongsTo(actor, workspace),
    );
  }

  static Future<Result<BaseModel<TenancyInvitation>, Failure>> create(
    CreateTenancyInvitationBody body,
  ) async {
    final failure = _accessFailure();
    if (failure != null) return Error(failure);
    final actor = accountId;
    if (!body.isValid || body.tenantId == actor) {
      return Error(ServerFailure(LocaleKeys.paidInvalidResponse));
    }
    return PremiumApiData.mutate(
      endpoint: TenancyInvitationApi.collection,
      body: body.toJson(),
      fromJson: TenancyInvitation.fromJson,
      valid: (item) =>
          item.hasValidIdentity &&
          item.propertyId == body.propertyId &&
          item.tenantId == body.tenantId &&
          item.ownerId == actor &&
          item.offerId == body.offerId &&
          item.status == TenancyInvitationStatus.pending &&
          !item.isExpired &&
          !item.eligibleForLease &&
          item.leaseId.isEmpty &&
          (body.offerId.isEmpty ||
              item.rentalSelection?.offerRevision ==
                  body.expectedOfferRevision),
    );
  }

  static Future<Result<BaseModel<TenancyInvitation>, Failure>> respond({
    required TenancyInvitation invitation,
    required TenancyInvitationStatus decision,
    required String requestKey,
  }) async {
    final failure = _accessFailure();
    if (failure != null) return Error(failure);
    if (!invitation.canRespondAs(accountId) ||
        requestKey.isEmpty ||
        (decision != TenancyInvitationStatus.accepted &&
            decision != TenancyInvitationStatus.rejected)) {
      return Error(ServerFailure(LocaleKeys.tenancyInvitationCannotRespond));
    }
    return PremiumApiData.mutate(
      endpoint: TenancyInvitationApi.respond(invitation.id),
      body: RespondTenancyInvitationBody(
        decision: decision,
        revision: invitation.revision,
        requestKey: requestKey,
      ).toJson(),
      fromJson: TenancyInvitation.fromJson,
      valid: (item) =>
          item.hasValidIdentity &&
          item.id == invitation.id &&
          item.propertyId == invitation.propertyId &&
          item.ownerId == invitation.ownerId &&
          item.tenantId == invitation.tenantId &&
          item.offerId == invitation.offerId &&
          item.status == decision &&
          item.revision > invitation.revision &&
          !item.canRespond &&
          (invitation.rentalSelection == null ||
              item.rentalSelection?.sameTermsAs(invitation.rentalSelection!) ==
                  true),
    );
  }
}
