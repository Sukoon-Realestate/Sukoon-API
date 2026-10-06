part of '../../imports.dart';

class SupportTicketsScreen extends StatelessWidget {
  const SupportTicketsScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.supportMyTickets,
    body: SafeArea(child: SupportTicketsList(workspace: workspace)),
  );
}
