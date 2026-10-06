part of '../../../imports.dart';

class OwnerProfileContentView extends StatelessWidget {
  const OwnerProfileContentView({
    super.key,
    required this.profile,
    required this.onEditPressed,
  });

  final OwnerProfileContent profile;
  final VoidCallback onEditPressed;

  @override
  Widget build(BuildContext context) {
    return ProfileContentView(
      workspace: AppWorkspace.owner,
      header: OwnerProfileHeaderCard(
        profile: profile,
        onEditPressed: onEditPressed,
      ),
      accountDetails: profile.accountDetails,
      isVerified: profile.owner.isVerified,
      activity: const OwnerProfileActions(),
      additionalSections: [
        ProfileVerificationBanner(
          title: '',
          description: profile.privacyNotice.text.isNotEmpty
              ? profile.privacyNotice.text
              : LocaleKeys.profileOwnerPhonePrivacy,
          isPrivacy: true,
        ),
        OwnerReviewsCard(reviews: profile.recentReviews),
      ],
    );
  }
}
