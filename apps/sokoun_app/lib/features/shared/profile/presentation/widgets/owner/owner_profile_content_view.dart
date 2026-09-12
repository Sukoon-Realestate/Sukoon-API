part of '../../../imports.dart';

class OwnerProfileContentView extends StatelessWidget {
  const OwnerProfileContentView({super.key, required this.profile});

  final OwnerProfileContent profile;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: EdgeInsets.fromLTRB(20.w, 14.h, 20.w, 24.h),
      children: [
        OwnerProfileHeaderCard(profile: profile),
        14.szH,
        ProfileAccountDetailsCard(details: profile.accountDetails),
        14.szH,
        ProfileVerificationBanner(
          title: '',
          description: profile.privacyNotice.text.isNotEmpty
              ? profile.privacyNotice.text
              : LocaleKeys.profileOwnerPhonePrivacy,
          isPrivacy: true,
        ),
        14.szH,
        OwnerReviewsCard(reviews: profile.recentReviews),
        14.szH,
        const ProfileDeleteAccountButton(),
      ],
    );
  }
}
