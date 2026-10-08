import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/base_crud/code/presentation/cubit/base_cubit/async_cubit.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import '../../data/enums/tenancy_invitation_status.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitations_data.dart';
import '../cubits/tenancy_invitation_response_cubit.dart';

class TenancyInvitationResponseActions extends StatelessWidget {
  const TenancyInvitationResponseActions({
    super.key,
    required this.invitation,
    required this.isFresh,
    required this.onRefresh,
  });
  final TenancyInvitation invitation;
  final bool isFresh;
  final Future<void> Function() onRefresh;

  Future<void> _respond(
    BuildContext context,
    TenancyInvitationStatus decision,
  ) async {
    final accepting = decision == TenancyInvitationStatus.accepted;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: AppText(
          accepting
              ? LocaleKeys.tenancyAcceptInvitation
              : LocaleKeys.tenancyRejectInvitation,
        ),
        content: AppText(
          accepting
              ? LocaleKeys.tenancyAcceptConfirmation
              : LocaleKeys.tenancyRejectConfirmation,
        ),
        actions: [
          TextButton(
            onPressed: () => Go.back(false),
            child: AppText(LocaleKeys.tenancyCancel),
          ),
          FilledButton(
            onPressed: () => Go.back(true),
            child: AppText(
              accepting
                  ? LocaleKeys.tenancyAcceptInvitation
                  : LocaleKeys.tenancyRejectInvitation,
            ),
          ),
        ],
      ),
    );
    if (confirmed != true || !context.mounted || !isFresh) return;
    await context.read<TenancyInvitationResponseCubit>().respond(
      invitation,
      decision,
    );
    if (context.mounted) await onRefresh();
  }

  @override
  Widget build(BuildContext context) =>
      BlocBuilder<
        TenancyInvitationResponseCubit,
        AsyncState<TenancyInvitation>
      >(
        builder: (context, state) {
          final canRespond =
              isFresh &&
              !state.isLoading &&
              invitation.canRespondAs(TenancyInvitationsData.accountId);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            spacing: 12,
            children: [
              if (invitation.canRespondAs(
                TenancyInvitationsData.accountId,
              )) ...[
                FilledButton.icon(
                  onPressed: canRespond
                      ? () =>
                            _respond(context, TenancyInvitationStatus.accepted)
                      : null,
                  icon: state.isLoading
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.check),
                  label: AppText(LocaleKeys.tenancyAcceptInvitation),
                ),
                OutlinedButton(
                  onPressed: canRespond
                      ? () =>
                            _respond(context, TenancyInvitationStatus.rejected)
                      : null,
                  child: AppText(LocaleKeys.tenancyRejectInvitation),
                ),
              ],
              if (state.isError && state.msg?.isNotEmpty == true)
                AppText(state.msg!),
            ],
          );
        },
      );
}
