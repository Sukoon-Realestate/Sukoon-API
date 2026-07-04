import 'package:flutter/widgets.dart';

/// Dont forget to add the font to pubspec
///
/// - family: Riyal
///   fonts:
///     - asset: assets/fonts/riyal.ttf
///


const IconData saudiRiyalSymbolIconData = IconData(0xe800, fontFamily: 'Riyal');
class RiyalPriceText extends StatelessWidget {
  final String price;
  final TextStyle? priceTextStyle;
  final TextStyle? currencyTextStyle;

  const RiyalPriceText(
      {super.key,
      required this.price,
      this.priceTextStyle,
      this.currencyTextStyle});

  bool checkIfPriceOnly() {
    final regx = RegExp(r'(\d+\.\d+)');
    return regx.hasMatch(price);
  }

  String getPrice() {
    return price;
  }

  @override
  Widget build(BuildContext context) {
    return RichText(
        textHeightBehavior: const TextHeightBehavior(
          applyHeightToFirstAscent: false,
          applyHeightToLastDescent: false,
        ),
        text: TextSpan(

      children: [
        TextSpan(
          text: "${getPrice()} ",
              style: priceTextStyle,
        ),
        WidgetSpan(
          child: Text(
                String.fromCharCode(saudiRiyalSymbolIconData.codePoint),
                style: (currencyTextStyle?.copyWith(
                  fontFamily: saudiRiyalSymbolIconData.fontFamily,
                ) ??
                priceTextStyle?.copyWith(
                  fontFamily: saudiRiyalSymbolIconData.fontFamily,
                ) ??
                TextStyle(
                  fontFamily: saudiRiyalSymbolIconData.fontFamily,
                        ))
                    .copyWith(height: 1
                ),
          ),
        ),
      ],
    ));
  }
}


extension RiyalPrice on Text {

  Widget withRiyalPrice() {
    return RiyalPriceText(
        price: data.toString(),
        priceTextStyle: style,
        currencyTextStyle: style);
  }
}
