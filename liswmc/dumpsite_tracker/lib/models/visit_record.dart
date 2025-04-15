class VisitRecord {
  final int? id;
  final int vehicleId;
  final DateTime entryTime;
  final DateTime? exitTime;
  final int? neighborhoodId;
  final String? wasteType;
  final String? notes;
  final String? createdBy;
  final String? imageUrl;
  final bool offlineCreated;
  final String syncStatus;
  
  // Join fields (not stored in database)
  final String? licensePlate;
  final String? companyName;
  final String? neighborhoodName;

  VisitRecord({
    this.id,
    required this.vehicleId,
    required this.entryTime,
    this.exitTime,
    this.neighborhoodId,
    this.wasteType,
    this.notes,
    this.createdBy,
    this.imageUrl,
    this.offlineCreated = false,
    this.syncStatus = 'Synced',
    this.licensePlate,
    this.companyName,
    this.neighborhoodName,
  });

  factory VisitRecord.fromMap(Map<String, dynamic> map) {
    return VisitRecord(
      id: map['id'],
      vehicleId: map['vehicle_id'],
      entryTime: map['entry_time'] is DateTime 
          ? map['entry_time'] 
          : DateTime.parse(map['entry_time']),
      exitTime: map['exit_time'] != null 
          ? map['exit_time'] is DateTime 
              ? map['exit_time'] 
              : DateTime.parse(map['exit_time'])
          : null,
      neighborhoodId: map['neighborhood_id'],
      wasteType: map['waste_type'],
      notes: map['notes'],
      createdBy: map['created_by'],
      imageUrl: map['image_url'],
      offlineCreated: map['offline_created'] ?? false,
      syncStatus: map['sync_status'] ?? 'Synced',
      licensePlate: map['license_plate'],
      companyName: map['company_name'],
      neighborhoodName: map['neighborhood_name'],
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'vehicle_id': vehicleId,
      'entry_time': entryTime.toIso8601String(),
      'exit_time': exitTime?.toIso8601String(),
      'neighborhood_id': neighborhoodId,
      'waste_type': wasteType,
      'notes': notes,
      'created_by': createdBy,
      'image_url': imageUrl,
      'offline_created': offlineCreated,
      'sync_status': syncStatus,
    };
  }

  @override
  String toString() {
    return 'VisitRecord(id: $id, vehicleId: $vehicleId, licensePlate: $licensePlate, entryTime: $entryTime)';
  }
}