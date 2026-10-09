import 'package:melos_core/core/local_db/read_cache_policy.dart';
import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:pagify/pagify.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import '../../data/models/tenancy_invitation.dart';
import '../../data/tenancy_invitation_capabilities.dart';
import '../../data/tenancy_invitations_data.dart';
import 'tenancy_invitation_card.dart';
import 'tenancy_invitations_unavailable.dart';
import 'tenancy_invitations_empty_state.dart';

class TenancyInvitationsList extends StatefulWidget {
  const TenancyInvitationsList({
    super.key,
    required this.workspace,
    this.propertyId = '',
  });
  final AppWorkspace workspace;
  final String propertyId;
  @override
  State<TenancyInvitationsList> createState() => _TenancyInvitationsListState();
}

class _TenancyInvitationsListState extends State<TenancyInvitationsList> {
  final PagifyController<TenancyInvitation> _controller = PagifyController();
  @override
  Widget build(BuildContext context) =>
      !TenancyInvitationCapabilities.current.enabled
      ? const SingleChildScrollView(
          padding: EdgeInsets.all(20),
          child: TenancyInvitationsUnavailable(),
        )
      : AppPagify<TenancyInvitation>(
          pagifyController: _controller,
          enablePullRefresh: true,
          header: Padding(
            padding: const EdgeInsets.all(20),
            child: AppText(LocaleKeys.tenancyInvitationsEntryBody),
          ),
          cacheKey: TenancyInvitationsData.cacheKey(
            widget.workspace,
            propertyId: widget.propertyId,
          ),
          cachePolicy: ReadCachePolicy.privateMemory,
          cacheToJson: (item) => item.toJson(),
          cacheFromJson: TenancyInvitation.fromJson,
          asyncCall: (_, page) => TenancyInvitationsData.getPage(
            page: page,
            workspace: widget.workspace,
            propertyId: widget.propertyId,
          ),
          emptyListView: const TenancyInvitationsEmptyState(),
          itemBuilder: (_, __, ___, item) => TenancyInvitationCard(
            key: ValueKey(item.id),
            invitation: item,
            workspace: widget.workspace,
            onReturned: _controller.refresh,
          ),
        );
}
