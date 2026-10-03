part of '../../imports.dart';

class SupportNewTicketScreen extends StatelessWidget {
  const SupportNewTicketScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.supportNewTicket,
    contentWidth: SokounContentWidth.form,
    body: SupportTicketForm(workspace: workspace),
  );
}
