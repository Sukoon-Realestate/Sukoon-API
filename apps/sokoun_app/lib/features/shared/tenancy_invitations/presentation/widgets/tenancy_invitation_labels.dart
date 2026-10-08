import 'package:melos_core/config/language/locale_keys.g.dart';
import '../../data/enums/tenancy_invitation_status.dart';
import '../../data/models/tenancy_invitation.dart';

abstract final class TenancyInvitationLabels {
  static String status(TenancyInvitation invitation) {
    final status =
        invitation.isExpired &&
            invitation.leaseId.isEmpty &&
            (invitation.status == TenancyInvitationStatus.pending ||
                invitation.status == TenancyInvitationStatus.accepted)
        ? TenancyInvitationStatus.expired
        : invitation.status;
    return switch (status) {
      TenancyInvitationStatus.pending => LocaleKeys.tenancyInvitationPending,
      TenancyInvitationStatus.accepted => LocaleKeys.tenancyInvitationAccepted,
      TenancyInvitationStatus.rejected => LocaleKeys.tenancyInvitationRejected,
      TenancyInvitationStatus.revoked => LocaleKeys.tenancyInvitationRevoked,
      TenancyInvitationStatus.expired => LocaleKeys.tenancyInvitationExpired,
      TenancyInvitationStatus.unknown => LocaleKeys.tenancyInvitationUnknown,
    };
  }
}
