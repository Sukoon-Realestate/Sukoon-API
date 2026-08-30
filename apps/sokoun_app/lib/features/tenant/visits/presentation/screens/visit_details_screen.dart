part of '../../imports.dart';

class VisitDetailsScreen extends StatelessWidget {
  const VisitDetailsScreen({super.key, required this.visit});

  final TenantVisitContent visit;

  void _openChat() {
    Go.to(ChatThreadScreen(conversation: ChatContent.conversations.first));
  }

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        backgroundColor: AppColors.scaffoldBackground,
        body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              VisitHeader(
                title: LocaleKeys.tenantVisitDetailsTitle,
                backKey: const ValueKey('visit-details-back'),
                onBackPressed: () => Go.back(),
              ),
              Expanded(
                child: VisitDetailsContent(
                  visit: visit,
                  onOpenChatPressed: _openChat,
                  onCancelVisitPressed: () => Go.back(true),
                  onFindAlternativePressed: () =>
                      Go.to(const TenantSearchScreen()),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
