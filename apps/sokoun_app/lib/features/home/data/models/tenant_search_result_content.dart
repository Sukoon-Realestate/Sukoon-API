import 'package:flutter/material.dart';
import 'package:melos_core/config/res/config_imports.dart';

class ActiveFilterContent {
  const ActiveFilterContent({required this.label});

  final String label;
}

class SearchResultContent {
  const SearchResultContent({
    required this.title,
    required this.location,
    required this.rooms,
    required this.bathrooms,
    required this.area,
    required this.tags,
    required this.price,
    required this.imageColor,
    required this.imageColorEnd,
    required this.isVerified,
  });

  final String title;
  final String location;
  final String rooms;
  final String bathrooms;
  final String area;
  final List<String> tags;
  final String price;
  final Color imageColor;
  final Color imageColorEnd;
  final bool isVerified;
}

abstract final class TenantSearchResultContent {
  static const activeFilters = [
    ActiveFilterContent(label: 'شقة'),
    ActiveFilterContent(label: 'مدينة نصر'),
    ActiveFilterContent(label: '6 شهور'),
    ActiveFilterContent(label: 'عائلات'),
    ActiveFilterContent(label: 'ممنوع التدخين'),
    ActiveFilterContent(label: 'أسانسير'),
  ];

  static const results = [
    SearchResultContent(
      title: 'شقة مفروشة 3 غرف',
      location: 'مدينة نصر، القاهرة',
      rooms: '3 غرف',
      bathrooms: '2 حمام',
      area: '90م²',
      tags: ['عائلات', 'أسانسير', 'ممنوع التدخين'],
      price: '6,500',
      imageColor: AppColors.sokoonTeal,
      imageColorEnd: AppColors.tealAlpha80,
      isVerified: false,
    ),
    SearchResultContent(
      title: 'ستوديو واسع',
      location: 'التجمع الخامس، القاهرة',
      rooms: '1 غرفة',
      bathrooms: '1 حمام',
      area: '55م²',
      tags: ['فردي', 'قريبة من المترو'],
      price: '3,200',
      imageColor: AppColors.blue,
      imageColorEnd: AppColors.blueGrayLight,
      isVerified: true,
    ),
    SearchResultContent(
      title: 'غرفة مفروشة',
      location: 'مصر الجديدة، القاهرة',
      rooms: '1 غرفة',
      bathrooms: '1 حمام',
      area: '30م²',
      tags: ['بنات فقط', 'ممنوع التدخين'],
      price: '1,800',
      imageColor: AppColors.rose,
      imageColorEnd: AppColors.roseAlpha19,
      isVerified: false,
    ),
    SearchResultContent(
      title: 'شقة 4 غرف فيلا',
      location: 'الشيخ زايد، الجيزة',
      rooms: '4 غرف',
      bathrooms: '3 حمام',
      area: '200م²',
      tags: ['عائلات', 'جراج', 'أسانسير'],
      price: '12,000',
      imageColor: AppColors.gold,
      imageColorEnd: AppColors.goldAlpha15,
      isVerified: true,
    ),
  ];
}
