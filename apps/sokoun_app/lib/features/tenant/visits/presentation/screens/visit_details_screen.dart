part of '../../imports.dart';

class VisitDetailsScreen extends StatelessWidget {
  const VisitDetailsScreen({super.key, required this.visit});

  final TenantVisitContent visit;

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: LocaleKeys.tenantVisitDetailsTitle,
      showBackButton: true,
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(child: VisitDetailsContent(visit: visit)),
    );
  }
}
