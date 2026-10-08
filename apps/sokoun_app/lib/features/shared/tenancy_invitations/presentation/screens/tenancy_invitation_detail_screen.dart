import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/premium_remote_view.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitation_capabilities.dart';
import '../cubits/tenancy_invitation_details_cubit.dart';
import '../cubits/tenancy_invitation_response_cubit.dart';
import '../widgets/tenancy_invitation_details.dart';
import '../widgets/tenancy_invitations_unavailable.dart';

class TenancyInvitationDetailScreen extends StatefulWidget {
  const TenancyInvitationDetailScreen({
    super.key,
    required this.invitationId,
    required this.workspace,
  });
  final String invitationId;
  final AppWorkspace workspace;
  @override
  State<TenancyInvitationDetailScreen> createState() =>
      _TenancyInvitationDetailScreenState();
}

class _TenancyInvitationDetailScreenState
    extends State<TenancyInvitationDetailScreen> {
  late final TenancyInvitationDetailsCubit _details;
  late final TenancyInvitationResponseCubit _response;
  late final Future<void> _request;
  @override
  void initState() {
    super.initState();
    _details = TenancyInvitationDetailsCubit();
    _response = TenancyInvitationResponseCubit();
    _request = TenancyInvitationCapabilities.current.enabled
        ? _load()
        : Future<void>.value();
  }

  Future<void> _load() => _details.load(widget.invitationId, widget.workspace);
  @override
  void dispose() {
    _details.close();
    _response.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => BlocProvider.value(
    value: _response,
    child:
        BlocSelector<
          TenancyInvitationResponseCubit,
          AsyncState<TenancyInvitation>,
          bool
        >(
          selector: (state) => state.isLoading,
          builder: (context, isResponding) => PopScope(
            canPop: !isResponding,
            child: AppScaffold(
              title: LocaleKeys.tenancyInvitationDetails,
              showBackButton: true,
              isBackEnabled: !isResponding,
              body: SafeArea(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(20),
                  child: SokounContent(
                    child: !TenancyInvitationCapabilities.current.enabled
                        ? const TenancyInvitationsUnavailable()
                        : PremiumRemoteView<
                            TenancyInvitationDetailsCubit,
                            TenancyInvitation
                          >(
                            cubit: _details,
                            request: _request,
                            initialData: const TenancyInvitation.initial(),
                            onRetry: _load,
                            builder: (invitation) => TenancyInvitationDetails(
                              invitation: invitation,
                              workspace: widget.workspace,
                              isFresh: !_details.isCached,
                              onRefresh: _load,
                            ),
                          ),
                  ),
                ),
              ),
            ),
          ),
        ),
  );
}
