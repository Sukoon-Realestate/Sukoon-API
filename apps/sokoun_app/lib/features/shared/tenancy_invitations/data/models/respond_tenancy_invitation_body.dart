import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/shared/premium/data/premium_json.dart';
import '../enums/tenancy_invitation_status.dart';

class RespondTenancyInvitationBody extends Equatable {
  const RespondTenancyInvitationBody({
    this.decision = TenancyInvitationStatus.unknown,
    this.revision = 0,
    this.requestKey = '',
  });
  const RespondTenancyInvitationBody.initial() : this();
  factory RespondTenancyInvitationBody.fromJson(Map<String, dynamic> json) =>
      RespondTenancyInvitationBody(
        decision: TenancyInvitationStatus.fromJson(json['decision']),
        revision: premiumInt(json['revision']) ?? 0,
        requestKey: premiumString(json['request_key']),
      );
  final TenancyInvitationStatus decision;
  final int revision;
  final String requestKey;
  Map<String, dynamic> toJson() => {
    'decision': decision.name,
    'revision': revision,
    'request_key': requestKey,
  };
  @override
  List<Object?> get props => [decision, revision, requestKey];
}
