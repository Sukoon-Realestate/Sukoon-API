import 'package:flutter/material.dart';

extension CenterWidget on Widget {
  Center get centerWidget => Center(child: this);
}

extension EndWidget on Widget {
  Align get endWidget => Align(
      alignment: AlignmentDirectional.centerEnd,
      child: this);
}
extension StartWidget on Widget {
  Align get startWidget => Align(
      alignment: AlignmentDirectional.centerStart,
      child: this);
}