import 'package:uuid/uuid.dart';
import 'package:sokoun_app/features/shared/premium/presentation/cubits/premium_mutation_cubit.dart';
import '../../data/enums/tenancy_invitation_status.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitations_data.dart';

class TenancyInvitationResponseCubit
    extends PremiumMutationCubit<TenancyInvitation> {
  TenancyInvitationResponseCubit() : super(const TenancyInvitation.initial());
  final Map<(String, int, TenancyInvitationStatus), String> _requestKeys = {};
  Future<TenancyInvitation?> respond(
    TenancyInvitation invitation,
    TenancyInvitationStatus decision,
  ) => perform(
    () => TenancyInvitationsData.respond(
      invitation: invitation,
      decision: decision,
      requestKey: _requestKeys.putIfAbsent((
        invitation.id,
        invitation.revision,
        decision,
      ), () => const Uuid().v4()),
    ),
  );
}
