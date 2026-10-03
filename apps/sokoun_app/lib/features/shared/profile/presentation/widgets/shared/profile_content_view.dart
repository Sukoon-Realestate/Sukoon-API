part of '../../../imports.dart';

class ProfileContentView extends StatelessWidget {
  const ProfileContentView({
    super.key,
    required this.workspace,
    required this.header,
    required this.accountDetails,
    required this.isVerified,
    required this.activity,
    this.verificationSubtitle,
    this.additionalSections = const [],
  });

  final AppWorkspace workspace;
  final Widget header;
  final ProfileAccountDetailsContent accountDetails;
  final bool isVerified;
  final String? verificationSubtitle;
  final Widget activity;
  final List<Widget> additionalSections;

  @override
  Widget build(BuildContext context) => ListView(
    padding: EdgeInsets.fromLTRB(20.w, 4.h, 20.w, 24.h),
    children: [
      header,
      14.szH,
      ProfileVerificationTile(
        workspace: workspace,
        isVerified: isVerified,
        subtitle: verificationSubtitle,
      ),
      14.szH,
      ProfileAccountDetailsCard(details: accountDetails),
      14.szH,
      activity,
      for (final section in additionalSections) ...[14.szH, section],
    ],
  );
}
