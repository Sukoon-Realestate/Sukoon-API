part of '../../imports.dart';

class OwnerRequestDetailsScreen extends StatelessWidget {
  const OwnerRequestDetailsScreen({super.key, required this.request});

  final OwnerVisitRequestContent request;

  Future<void> _acceptRequest(BuildContext context) async {
    final bool? confirmed = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: AppColors.transparent,
      barrierColor: AppColors.blackAlpha45,
      builder: (context) => OwnerAcceptRequestSheet(request: request),
    );

    if (confirmed == true && context.mounted) {
      Go.back(OwnerRequestResolution.accepted);
    }
  }

  Future<void> _rejectRequest(BuildContext context) async {
    final OwnerRejectionReason? reason =
        await showModalBottomSheet<OwnerRejectionReason>(
          context: context,
          isScrollControlled: true,
          useSafeArea: true,
          backgroundColor: AppColors.transparent,
          barrierColor: AppColors.blackAlpha45,
          builder: (context) => const OwnerRejectRequestSheet(),
        );

    if (reason != null && context.mounted) {
      Go.back(OwnerRequestResolution.rejected);
    }
  }

  void _openChat() {
    Go.to(
      ChatThreadScreen(
        conversation: ConversationContent(
          id: 101,
          name: request.name,
          property: request.property,
          lastMessage: request.tenantNote,
          time: request.time,
          unreadCount: 0,
          isVerified: request.isVerified,
          isOnline: true,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            children: [
              VisitHeader(
                title: LocaleKeys.ownerRequestDetailsTitle,
                backKey: const ValueKey('owner-request-details-back'),
                onBackPressed: () => Go.back(),
              ),
              Expanded(
                child: OwnerRequestDetailsContent(
                  request: request,
                  onAcceptPressed: () => _acceptRequest(context),
                  onRejectPressed: () => _rejectRequest(context),
                  onChatPressed: _openChat,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
