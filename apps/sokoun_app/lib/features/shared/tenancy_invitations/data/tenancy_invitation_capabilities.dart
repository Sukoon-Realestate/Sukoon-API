import 'package:melos_core/config/res/config_imports.dart' show injector;

/// Proposed API: enable only after the backend handoff and staging verification.
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
