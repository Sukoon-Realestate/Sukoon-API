import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/verified_action_cubit.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitations_data.dart';

class TenancyInvitationDetailsCubit
    extends VerifiedActionCubit<TenancyInvitation> {
  TenancyInvitationDetailsCubit() : super(const TenancyInvitation.initial());
  bool _isCached = true;
  bool get isCached => _isCached;
  Future<void> load(String id, AppWorkspace workspace) async {
    if (isClosed || isLoading || id.isEmpty) return;
    _isCached = true;
    await executeAsyncWithBaseModel(
      operation: () => TenancyInvitationsData.get(id: id, workspace: workspace),
      withInternetInterceptor: true,
      onSuccess: (response) => _isCached = response.key == 'fromCache',
    );
  }
}
