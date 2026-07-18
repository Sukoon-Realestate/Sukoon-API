import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/widgets/buttons/default_button.dart';
import 'package:sokoun_app/features/auth/data/social_auth_service/google_sign_in.dart';

class AppGoogleSignInButton extends StatelessWidget {
  const AppGoogleSignInButton({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultButton(
      onTap: ()async{
        await GoogleSignService.instance.init();
        await GoogleSignService.instance.authorize();
      },
      color: AppColors.white,
      borderColor: AppColors.sokoonBorder,
      borderRadius: BorderRadius.circular(12.r),
      height: 48.h,
      width: double.infinity,
      customChild: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 20.r,
            height: 20.r,
            child: const CustomPaint(painter: _GoogleMarkPainter()),
          ),
          SizedBox(width: 10.w),
          Flexible(
            child: AppText(
              LocaleKeys.continueWithGoogle,
              color: AppColors.sokoonNavy,
              fontSize: 14.sp,
              fontWeight: FontWeight.w700,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _GoogleMarkPainter extends CustomPainter {
  const _GoogleMarkPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final stroke = size.width * .18;
    final rect =
        Offset(stroke / 2, stroke / 2) &
        Size(size.width - stroke, size.height - stroke);
    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round;

    paint.color = const Color(0xFF4285F4);
    canvas.drawArc(rect, -.1, 1.55, false, paint);
    paint.color = const Color(0xFF34A853);
    canvas.drawArc(rect, 1.45, 1.35, false, paint);
    paint.color = const Color(0xFFFBBC05);
    canvas.drawArc(rect, 2.75, 1.1, false, paint);
    paint.color = const Color(0xFFEA4335);
    canvas.drawArc(rect, 3.85, 1.35, false, paint);

    final bluePaint = Paint()
      ..color = const Color(0xFF4285F4)
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.square;
    canvas.drawLine(
      Offset(size.width * .52, size.height * .5),
      Offset(size.width * .9, size.height * .5),
      bluePaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
