part of '../../../imports.dart';

class VisitRatingStars extends StatelessWidget {
  const VisitRatingStars({
    super.key,
    required this.rating,
    required this.onRatingSelected,
    this.size = 36,
  });

  final int rating;
  final ValueChanged<int> onRatingSelected;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      textDirection: TextDirection.ltr,
      children: [
        for (int star = 1; star <= 5; star++)
          IconButton(
            onPressed: () => onRatingSelected(star),
            visualDensity: VisualDensity.compact,
            constraints: BoxConstraints.tightFor(
              width: (size + 8).r,
              height: (size + 8).r,
            ),
            padding: EdgeInsets.zero,
            icon: Icon(
              star <= rating ? Icons.star_rounded : Icons.star_border_rounded,
              color: star <= rating ? AppColors.gold : AppColors.grayPale,
              size: size.r,
            ),
          ),
      ],
    );
  }
}
