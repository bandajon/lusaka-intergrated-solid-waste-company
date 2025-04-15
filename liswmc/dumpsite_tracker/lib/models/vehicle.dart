class Vehicle {
  final int? id;
  final String licensePlate;
  final int? companyId;
  final String? vehicleType;
  final String? vehicleImageUrl;
  final DateTime? registrationDate;
  final bool isTemporary;
  final DateTime? tempExpiryDate;
  final DateTime? lastVisitDate;
  
  // Join fields (not stored in database)
  final String? companyName;
  final String? companyType;

  Vehicle({
    this.id,
    required this.licensePlate,
    this.companyId,
    this.vehicleType,
    this.vehicleImageUrl,
    this.registrationDate,
    this.isTemporary = false,
    this.tempExpiryDate,
    this.lastVisitDate,
    this.companyName,
    this.companyType,
  });

  factory Vehicle.fromMap(Map<String, dynamic> map) {
    return Vehicle(
      id: map['id'],
      licensePlate: map['license_plate'],
      companyId: map['company_id'],
      vehicleType: map['vehicle_type'],
      vehicleImageUrl: map['vehicle_image_url'],
      registrationDate: map['registration_date'] != null 
          ? map['registration_date'] is DateTime 
              ? map['registration_date'] 
              : DateTime.parse(map['registration_date'])
          : null,
      isTemporary: map['is_temporary'] ?? false,
      tempExpiryDate: map['temp_expiry_date'] != null 
          ? map['temp_expiry_date'] is DateTime 
              ? map['temp_expiry_date'] 
              : DateTime.parse(map['temp_expiry_date'])
          : null,
      lastVisitDate: map['last_visit_date'] != null 
          ? map['last_visit_date'] is DateTime 
              ? map['last_visit_date'] 
              : DateTime.parse(map['last_visit_date'])
          : null,
      companyName: map['company_name'],
      companyType: map['company_type'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'license_plate': licensePlate,
      'company_id': companyId,
      'vehicle_type': vehicleType,
      'vehicle_image_url': vehicleImageUrl,
      'registration_date': registrationDate?.toIso8601String(),
      'is_temporary': isTemporary,
      'temp_expiry_date': tempExpiryDate?.toIso8601String(),
      'last_visit_date': lastVisitDate?.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'Vehicle(id: $id, licensePlate: $licensePlate, companyId: $companyId, companyName: $companyName, isTemporary: $isTemporary)';
  }
}