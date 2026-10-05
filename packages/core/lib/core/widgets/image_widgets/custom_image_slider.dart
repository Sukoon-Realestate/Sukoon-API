import 'dart:async';
import 'package:flutter/material.dart';

import '../../../config/res/config_imports.dart';
import '../../extensions/context_extension.dart';
import 'cached_image.dart';

class ImageSlider extends StatefulWidget {
  final Color? activeColor;
  final Color? inActiveColor;
  final List<String> images;
  final double? height, width;
  final bool showPointer;
  final BoxFit? fit;

  const ImageSlider({
    super.key,
    required this.images,
    this.activeColor,
    this.inActiveColor,
    this.height,
    this.width,
    this.showPointer = true,
    this.fit,
  });

  @override
  State<ImageSlider> createState() => _ImageSliderState();
}

class _ImageSliderState extends State<ImageSlider> {
  final ValueNotifier<int> _currentIndex = ValueNotifier<int>(0);
  final PageController _pageController = PageController();
  late Timer timer;

  @override
  void initState() {
    super.initState();
    _startAutoScroll();
  }

  void _startAutoScroll() {
    timer = Timer.periodic(const Duration(seconds: 3), (timer) {
      if (_currentIndex.value < widget.images.length - 1) {
        _currentIndex.value++;
      } else {
        _currentIndex.value = 0;
      }
      _pageController.animateToPage(
        _currentIndex.value,
        duration: const Duration(milliseconds: 800),
        curve: Curves.fastOutSlowIn,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      mainAxisAlignment: MainAxisAlignment.start,
      spacing: AppMargin.mH10,
      children: [
        SizedBox(
          height: widget.height,
          width: widget.width,
          child: PageView.builder(
            controller: _pageController,
            itemCount: widget.images.length,
            scrollDirection: Axis.horizontal,
            onPageChanged: (index) => _currentIndex.value = index,
            itemBuilder: (context, index) {
              return CachedImage(
                url: widget.images[index],
                width: widget.width ?? context.width,
                height: widget.height ?? context.height * .24,
              );
            },
          ),
        ),
        ValueListenableBuilder<int>(
          valueListenable: _currentIndex,
          builder: (context, value, child) {
            return Visibility(
              visible: widget.showPointer,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: widget.images.asMap().entries.map((entry) {
                  final index = entry.key;
                  final isActive = index == value;
                  return AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    width: AppSize.sH6,
                    height: AppSize.sH6,
                    margin: EdgeInsets.symmetric(horizontal: AppMargin.mW2),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(AppCircular.r20),
                      color: isActive
                          ? widget.activeColor ??
                                context.appColor(
                                  AppColors.primary,
                                  surface: true,
                                )
                          : widget.inActiveColor ?? Colors.grey,
                    ),
                  );
                }).toList(),
              ),
            );
          },
        ),
      ],
    );
  }

  @override
  void dispose() {
    _pageController.dispose();
    timer.cancel(); // Cancel the auto-scroll timer when the widget is disposed
    super.dispose();
  }
}
