import 'package:flutter/material.dart';

abstract class TransitionCreator {
  Widget animate(
    Animation<double> animation,
    Animation<double> secondaryAnimation,
    Widget child,
  );
}
