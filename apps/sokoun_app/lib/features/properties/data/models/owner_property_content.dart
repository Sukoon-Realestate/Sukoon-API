part of '../../imports.dart';

class OwnerPropertyContent {
  const OwnerPropertyContent({
    required this.id,
    required this.title,
    required this.location,
    required this.monthlyPrice,
    required this.views,
    required this.visitRequests,
    required this.bedrooms,
    required this.area,
    required this.description,
    required this.photoCount,
    required this.status,
    required this.icon,
  });

  factory OwnerPropertyContent.initial() {
    return const OwnerPropertyContent(
      id: '',
      title: '',
      location: '',
      monthlyPrice: 0,
      views: 0,
      visitRequests: 0,
      bedrooms: 0,
      area: 0,
      description: '',
      photoCount: 0,
      status: OwnerPropertyStatus.pending,
      icon: Icons.apartment_rounded,
    );
  }

  factory OwnerPropertyContent.fromJson(Map<String, dynamic> json) {
    return OwnerPropertyContent(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      location: json['location'] ?? '',
      monthlyPrice: json['monthly_price'] ?? 0,
      views: json['views'] ?? 0,
      visitRequests: json['visit_requests'] ?? 0,
      bedrooms: json['bedrooms'] ?? 0,
      area: json['area'] ?? 0,
      description: json['description'] ?? '',
      photoCount: json['photo_count'] ?? 0,
      status: OwnerPropertyStatusX.fromName(json['status']),
      icon: IconData(
        json['icon_code_point'] ?? Icons.apartment_rounded.codePoint,
        fontFamily: 'MaterialIcons',
      ),
    );
  }

  final String id;
  final String title;
  final String location;
  final int monthlyPrice;
  final int views;
  final int visitRequests;
  final int bedrooms;
  final int area;
  final String description;
  final int photoCount;
  final OwnerPropertyStatus status;
  final IconData icon;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'location': location,
      'monthly_price': monthlyPrice,
      'views': views,
      'visit_requests': visitRequests,
      'bedrooms': bedrooms,
      'area': area,
      'description': description,
      'photo_count': photoCount,
      'status': status.name,
      'icon_code_point': icon.codePoint,
    };
  }

  OwnerPropertyContent copyWith({
    String? id,
    String? title,
    String? location,
    int? monthlyPrice,
    int? views,
    int? visitRequests,
    int? bedrooms,
    int? area,
    String? description,
    int? photoCount,
    OwnerPropertyStatus? status,
    IconData? icon,
  }) {
    return OwnerPropertyContent(
      id: id ?? this.id,
      title: title ?? this.title,
      location: location ?? this.location,
      monthlyPrice: monthlyPrice ?? this.monthlyPrice,
      views: views ?? this.views,
      visitRequests: visitRequests ?? this.visitRequests,
      bedrooms: bedrooms ?? this.bedrooms,
      area: area ?? this.area,
      description: description ?? this.description,
      photoCount: photoCount ?? this.photoCount,
      status: status ?? this.status,
      icon: icon ?? this.icon,
    );
  }
}

abstract final class OwnerPropertiesContent {
  static List<OwnerPropertyContent> prototype() {
    return [
      OwnerPropertyContent(
        id: 'nasr-city-furnished',
        title: LocaleKeys.ownerPropertyNasrCityTitle,
        location: LocaleKeys.ownerPropertyNasrCityLocation,
        monthlyPrice: 6500,
        views: 142,
        visitRequests: 3,
        bedrooms: 2,
        area: 120,
        description: LocaleKeys.ownerPropertyNasrCityDescription,
        photoCount: 12,
        status: OwnerPropertyStatus.verified,
        icon: Icons.apartment_rounded,
      ),
      OwnerPropertyContent(
        id: 'fifth-settlement-studio',
        title: LocaleKeys.ownerPropertyStudioTitle,
        location: LocaleKeys.ownerPropertyStudioLocation,
        monthlyPrice: 4200,
        views: 67,
        visitRequests: 0,
        bedrooms: 1,
        area: 65,
        description: LocaleKeys.ownerPropertyStudioDescription,
        photoCount: 8,
        status: OwnerPropertyStatus.pending,
        icon: Icons.meeting_room_outlined,
      ),
      OwnerPropertyContent(
        id: 'mohandessin-three-bed',
        title: LocaleKeys.ownerPropertyMohandessinTitle,
        location: LocaleKeys.ownerPropertyMohandessinLocation,
        monthlyPrice: 8800,
        views: 0,
        visitRequests: 0,
        bedrooms: 3,
        area: 165,
        description: LocaleKeys.ownerPropertyMohandessinDescription,
        photoCount: 10,
        status: OwnerPropertyStatus.hidden,
        icon: Icons.home_work_outlined,
      ),
    ];
  }

  static OwnerPropertyContent rejectedPrototype() {
    return OwnerPropertyContent(
      id: 'nasr-city-rejected',
      title: LocaleKeys.ownerPropertyNasrCityTitle,
      location: LocaleKeys.ownerPropertyNasrCityLocation,
      monthlyPrice: 6500,
      views: 0,
      visitRequests: 0,
      bedrooms: 2,
      area: 120,
      description: LocaleKeys.ownerPropertyNasrCityDescription,
      photoCount: 12,
      status: OwnerPropertyStatus.rejected,
      icon: Icons.apartment_rounded,
    );
  }
}
