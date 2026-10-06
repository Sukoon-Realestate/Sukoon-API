part of '../../../imports.dart';

class ProfileIdentityHeader extends StatelessWidget {
  const ProfileIdentityHeader({
    super.key,
    required this.avatar,
    required this.details,
  });
  final Widget avatar;
  final Widget details;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      if (constraints.maxWidth < 340 &&
          MediaQuery.textScalerOf(context).scale(14) > 16) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          spacing: 12.h,
          children: [
            Align(alignment: AlignmentDirectional.centerStart, child: avatar),
            details,
          ],
        );
      }
      return Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        spacing: 14.w,
        children: [
          avatar,
          Expanded(child: details),
        ],
      );
    },
  );
}
