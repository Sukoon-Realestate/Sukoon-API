import 'package:melos_core/config/res/config_imports.dart' show injector;

/// Agreed API: keep disabled until staging deployment and verification.
/// See TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md for rollout status.
class TenancyInvitationCapabilities {
  const TenancyInvitationCapabilities({this.enabled = false});

  static const configured = TenancyInvitationCapabilities(
    enabled: bool.fromEnvironment('SOKOUN_TENANCY_INVITATIONS'),
  );

  static TenancyInvitationCapabilities get current =>
      injector.isRegistered<TenancyInvitationCapabilities>()
      ? injector<TenancyInvitationCapabilities>()
      : configured;

  final bool enabled;
}
