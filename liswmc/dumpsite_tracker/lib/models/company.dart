class Company {
  final int? id;
  final String name;
  final String type; // 'Franchise', 'Community', 'LISWMC', 'Private'
  final String? contactPerson;
  final String? contactNumber;
  final String? email;
  final DateTime? registrationDate;
  final String status;

  Company({
    this.id,
    required this.name,
    required this.type,
    this.contactPerson,
    this.contactNumber,
    this.email,
    this.registrationDate,
    this.status = 'Active',
  });

  factory Company.fromMap(Map<String, dynamic> map) {
    return Company(
      id: map['id'],
      name: map['name'],
      type: map['type'],
      contactPerson: map['contact_person'],
      contactNumber: map['contact_number'],
      email: map['email'],
      registrationDate: map['registration_date'] != null 
          ? map['registration_date'] is DateTime 
              ? map['registration_date'] 
              : DateTime.parse(map['registration_date'])
          : null,
      status: map['status'] ?? 'Active',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'name': name,
      'type': type,
      'contact_person': contactPerson,
      'contact_number': contactNumber,
      'email': email,
      'registration_date': registrationDate?.toIso8601String(),
      'status': status,
    };
  }

  @override
  String toString() {
    return 'Company(id: $id, name: $name, type: $type, contactPerson: $contactPerson, status: $status)';
  }
}