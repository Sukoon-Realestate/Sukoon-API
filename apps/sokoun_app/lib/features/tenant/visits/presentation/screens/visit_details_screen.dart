part of '../../imports.dart';

class VisitDetailsScreen extends StatelessWidget {
  const VisitDetailsScreen({super.key, required this.visit});

  final TenantVisitContent visit;

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
              VisitHeader(title: LocaleKeys.tenantVisitDetailsTitle),
              Expanded(child: VisitDetailsContent(visit: visit)),
            ],
          ),
        ),
      ),
    );
  }
}
