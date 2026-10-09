import 'package:equatable/equatable.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/enums/workspace_tab.dart';

enum DestinationKind {
  property,
  tenantVisit,
  tenantVisits,
  ownerRequest,
  ownerProperties,
  ownerListings,
  propertyAnalytics,
  chat,
  notifications,
  notificationDetail,
  profileVerification,
  profileSettings,
  searchAlert,
  tenancyInvitation,
  tenancyInvitations,
  externalPromotion,
}

class AppDestination extends Equatable {
  const AppDestination({
    required this.kind,
    this.id = '',
    this.offerId,
    this.workspace,
    this.tab,
    this.openReview = false,
    this.url,
  });
  final DestinationKind kind;
  final String id;
  final String? offerId;
  final AppWorkspace? workspace;
  final WorkspaceTab? tab;
  final bool openReview;
  final Uri? url;
  bool get requiresAccount =>
      kind != DestinationKind.property &&
      kind != DestinationKind.externalPromotion;
  String get identity =>
      '${kind.name}|$id|${offerId ?? ''}|${workspace?.name ?? ''}|$openReview';
  @override
  List<Object?> get props => [
    kind,
    id,
    offerId,
    workspace,
    tab,
    openReview,
    url,
  ];
}
