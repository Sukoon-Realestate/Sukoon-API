import 'dart:async';
import 'package:flutter/material.dart';
import '../../config/res/config_imports.dart';
import '../extensions/padding_extension.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import '../../config/language/locale_keys.g.dart';
import 'buttons/app_loading_button.dart';

enum OptionsRanking{vertical, horizontal}

// T is the dataType
class RadioSelectionWidget<T> extends StatefulWidget {
  final OptionsRanking ranking;
  final List<T> values;
  final List<Widget> titles;
  final String title;
  final TextStyle? titleTextStyle;
  final Alignment titleAlignment;
  final FutureOr<void> Function(BuildContext context, T val) onSubmit;
  final Color? btnColor;
  final String? btnTitle;
  final double? btnHeight;
  final T? initialValue;
  final bool showSubmitButton;
  final Color selectedBackgroundColor;
  final Color unSelectedBackgroundColor;

  const RadioSelectionWidget({super.key,
    required this.title,
    required this.onSubmit,
    required this.values,
    required this.titles,
    this.titleTextStyle,
    this.selectedBackgroundColor = AppColors.primary,
    this.unSelectedBackgroundColor = Colors.white,
    this.titleAlignment = Alignment.center,
    this.showSubmitButton = false,
    this.ranking = OptionsRanking.vertical,
    this.btnColor,
    this.btnTitle,
    this.btnHeight,
    this.initialValue,
  }) : assert(values.length == titles.length);

  @override
  State<RadioSelectionWidget<T>> createState() => _RadioSelectionWidgetState<T>();
}

class _RadioSelectionWidgetState<T> extends State<RadioSelectionWidget<T>> {
  T? groupValue;
  int _currentIndex = -1;

  void _changeValue({required int index, T? newVal}){
    setState(() {
      _currentIndex = index;
      groupValue = newVal;
    });

    if(!widget.showSubmitButton){
      widget.onSubmit.call(context, groupValue!);
    }
  }

  @override
  void initState() {
    groupValue = widget.initialValue;
    super.initState();
  }

  List<Widget> get _children =>  List.generate(
    widget.values.length,
        (index) => index != widget.values.length -1? _RadioItem<T?>(
      title: widget.titles[index],
      value: widget.values[index],
      groupValue: groupValue,
      isSelected: _currentIndex == index,
      selectedBackgroundColor: widget.selectedBackgroundColor,
      unSelectedBackgroundColor: widget.unSelectedBackgroundColor,
      onChanged: (newVal) => _changeValue(index: index, newVal: newVal),
    ) : Column(
      spacing: 10.h,
      children: [
        _RadioItem<T?>(
          isSelected: _currentIndex == index,
          selectedBackgroundColor: widget.selectedBackgroundColor,
          unSelectedBackgroundColor: widget.unSelectedBackgroundColor,
          title: widget.titles[index],
          value: widget.values[index],
          groupValue: groupValue,
          onChanged: (newVal) => _changeValue(index: index, newVal: newVal),
        ),
        if(widget.showSubmitButton)
          AppLoadingButton(
            title: widget.btnTitle?? LocaleKeys.confirm,
            asyncCall: (context) async => groupValue == null? null :
            await widget.onSubmit(context, groupValue as T),
            height: widget.btnHeight?? 40.h,
            buttonColor: groupValue == null?
            Colors.grey[300] : widget.btnColor ?? AppColors.primary,
          ),
      ],
    ),
  );

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(12.r)),
        ),
        child: Column(
          spacing: 16.h,
          children: [
            Align(
                alignment: widget.titleAlignment,
                child: Text(widget.title, style: widget.titleTextStyle)),
            if(widget.ranking == OptionsRanking.vertical)
              Column(
                spacing: 10.h,
                children: _children,
              )
            else
              Wrap(
                spacing: 10.w,
                runSpacing: 10.h,
                children: _children,
              )
          ],
        ).paddingAll(12.r),
      ),
    );
  }
}

class _RadioItem<T> extends StatelessWidget {
  final Widget title;
  final T value;
  final T groupValue;
  final void Function(T? val) onChanged;
  final bool isSelected;
  final Color selectedBackgroundColor;
  final Color unSelectedBackgroundColor;

  const _RadioItem({super.key,
    required this.title,
    required this.value,
    required this.groupValue,
    required this.onChanged,
    required this.isSelected,
    required this.selectedBackgroundColor,
    required this.unSelectedBackgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => onChanged.call(value),
      child: Container(
        padding: EdgeInsets.symmetric(vertical: 5.h, horizontal: 12.w),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(7.r),
          border: Border.all(
              color: isSelected?
              selectedBackgroundColor :
              Colors.grey
          ),
          color: isSelected?
          selectedBackgroundColor :
          unSelectedBackgroundColor,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Radio<T>(
              value: value,
              groupValue: groupValue,
              onChanged: onChanged,
              activeColor: AppColors.primary,
            ),
            title,
          ],
        ),
      ),
    );
  }
}
