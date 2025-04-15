import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/company.dart';
import '../../services/database_service.dart';
import '../../services/offline_sync_service.dart';

class CompanyRegistrationScreen extends StatefulWidget {
  final String initialCompanyType;
  final String vehicleLicensePlate;
  
  CompanyRegistrationScreen({
    required this.initialCompanyType,
    required this.vehicleLicensePlate,
  });
  
  @override
  _CompanyRegistrationScreenState createState() => _CompanyRegistrationScreenState();
}

class _CompanyRegistrationScreenState extends State<CompanyRegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _contactPersonController = TextEditingController();
  final TextEditingController _contactNumberController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  
  String _selectedCompanyType = '';
  bool _isLoading = false;
  
  @override
  void initState() {
    super.initState();
    _selectedCompanyType = widget.initialCompanyType;
  }
  
  @override
  void dispose() {
    _nameController.dispose();
    _contactPersonController.dispose();
    _contactNumberController.dispose();
    _emailController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Register Company'),
      ),
      body: _isLoading
        ? Center(child: CircularProgressIndicator())
        : SingleChildScrollView(
            padding: EdgeInsets.all(16.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Company Information',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                          ),
                          SizedBox(height: 8),
                          Text(
                            'For vehicle: ${widget.vehicleLicensePlate}',
                            style: TextStyle(
                              color: Colors.grey.shade700,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          SizedBox(height: 16),
                          
                          // Company name
                          TextFormField(
                            controller: _nameController,
                            decoration: InputDecoration(
                              labelText: 'Company Name',
                              border: OutlineInputBorder(),
                            ),
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Please enter company name';
                              }
                              return null;
                            },
                          ),
                          SizedBox(height: 16),
                          
                          // Company type
                          DropdownButtonFormField<String>(
                            value: _selectedCompanyType,
                            decoration: InputDecoration(
                              labelText: 'Company Type',
                              border: OutlineInputBorder(),
                            ),
                            items: ['Franchise', 'Community', 'LISWMC', 'Private']
                              .map((type) => DropdownMenuItem(
                                value: type,
                                child: Text(type),
                              ))
                              .toList(),
                            onChanged: (value) {
                              if (value != null) {
                                setState(() {
                                  _selectedCompanyType = value;
                                });
                              }
                            },
                            validator: (value) {
                              if (value == null || value.isEmpty) {
                                return 'Please select company type';
                              }
                              return null;
                            },
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  SizedBox(height: 16),
                  
                  Card(
                    elevation: 2,
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Contact Information',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
                          ),
                          SizedBox(height: 16),
                          
                          // Contact person
                          TextFormField(
                            controller: _contactPersonController,
                            decoration: InputDecoration(
                              labelText: 'Contact Person',
                              border: OutlineInputBorder(),
                            ),
                          ),
                          SizedBox(height: 16),
                          
                          // Contact number
                          TextFormField(
                            controller: _contactNumberController,
                            decoration: InputDecoration(
                              labelText: 'Contact Number',
                              border: OutlineInputBorder(),
                              prefixText: '+260 ',
                            ),
                            keyboardType: TextInputType.phone,
                          ),
                          SizedBox(height: 16),
                          
                          // Email
                          TextFormField(
                            controller: _emailController,
                            decoration: InputDecoration(
                              labelText: 'Email Address',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.emailAddress,
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  SizedBox(height: 24),
                  
                  ElevatedButton(
                    onPressed: _registerCompany,
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        'Register Company',
                        style: TextStyle(fontSize: 18),
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                    ),
                  ),
                ],
              ),
            ),
          ),
    );
  }
  
  Future<void> _registerCompany() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      final offlineSyncService = Provider.of<OfflineSyncService>(context, listen: false);
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      
      // Create company object
      final company = Company(
        name: _nameController.text,
        type: _selectedCompanyType,
        contactPerson: _contactPersonController.text.isNotEmpty
            ? _contactPersonController.text
            : null,
        contactNumber: _contactNumberController.text.isNotEmpty
            ? '+260 ${_contactNumberController.text}'
            : null,
        email: _emailController.text.isNotEmpty
            ? _emailController.text
            : null,
        registrationDate: DateTime.now(),
        status: 'Active',
      );
      
      final isOnline = await offlineSyncService.isOnline();
      Company registeredCompany;
      
      if (isOnline) {
        // Online - register in database
        final companyId = await databaseService.registerNewCompany(company);
        
        if (companyId > 0) {
          registeredCompany = company.copyWith(id: companyId);
        } else {
          throw Exception('Failed to register company');
        }
      } else {
        // Offline - save locally
        await offlineSyncService.saveCompanyOffline(company);
        registeredCompany = company;
      }
      
      // Return to previous screen with company data
      Navigator.pop(context, registeredCompany);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
      setState(() => _isLoading = false);
    }
  }
}

// Extension for copying
extension CompanyCopyWith on Company {
  Company copyWith({
    int? id,
    String? name,
    String? type,
    String? contactPerson,
    String? contactNumber,
    String? email,
    DateTime? registrationDate,
    String? status,
  }) {
    return Company(
      id: id ?? this.id,
      name: name ?? this.name,
      type: type ?? this.type,
      contactPerson: contactPerson ?? this.contactPerson,
      contactNumber: contactNumber ?? this.contactNumber,
      email: email ?? this.email,
      registrationDate: registrationDate ?? this.registrationDate,
      status: status ?? this.status,
    );
  }
}