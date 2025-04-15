import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../models/vehicle.dart';
import '../../models/company.dart';
import '../../models/neighborhood.dart';
import '../../models/visit_record.dart';
import '../../services/license_plate_service.dart';
import '../../services/database_service.dart';
import '../../services/offline_sync_service.dart';
import '../company_registration/company_registration_screen.dart';

class VehicleEntryScreen extends StatefulWidget {
  @override
  _VehicleEntryScreenState createState() => _VehicleEntryScreenState();
}

class _VehicleEntryScreenState extends State<VehicleEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _licensePlateController = TextEditingController();
  final TextEditingController _neighborhoodController = TextEditingController();
  final TextEditingController _wasteTypeController = TextEditingController();
  final TextEditingController _notesController = TextEditingController();
  
  final LicensePlateService _licensePlateService = LicensePlateService();
  
  Vehicle? _selectedVehicle;
  Company? _selectedCompany;
  Neighborhood? _selectedNeighborhood;
  File? _vehicleImage;
  String? _savedImagePath;
  
  bool _isLoading = false;
  bool _isSearching = false;
  bool _isNewVehicle = false;
  List<Vehicle> _searchResults = [];
  List<Neighborhood> _neighborhoodResults = [];
  
  @override
  void dispose() {
    _licensePlateController.dispose();
    _neighborhoodController.dispose();
    _wasteTypeController.dispose();
    _notesController.dispose();
    _licensePlateService.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Vehicle Entry'),
        actions: [
          IconButton(
            icon: Icon(Icons.sync),
            onPressed: () async {
              final offlineSyncService = Provider.of<OfflineSyncService>(context, listen: false);
              await offlineSyncService.syncOfflineRecords();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Sync initiated')),
              );
            },
          ),
        ],
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
                  // License plate input with camera button and search
                  _buildLicensePlateInput(),
                  
                  // Vehicle search results
                  if (_isSearching)
                    _buildSearchResults(),
                  
                  // Vehicle details section
                  if (_selectedVehicle != null || _isNewVehicle)
                    _buildVehicleDetailsSection(),
                  
                  // Neighborhood selection
                  _buildNeighborhoodInput(),
                  
                  // Vehicle image section
                  _buildVehicleImageSection(),
                  
                  // Additional info section
                  _buildAdditionalInfoSection(),
                  
                  // Submit button
                  SizedBox(height: 20),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _submitEntry,
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 12),
                      child: Text(
                        'Record Vehicle Entry',
                        style: TextStyle(fontSize: 18),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
    );
  }
  
  Widget _buildLicensePlateInput() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'License Plate',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _licensePlateController,
                    textCapitalization: TextCapitalization.characters,
                    decoration: InputDecoration(
                      hintText: 'Enter license plate',
                      border: OutlineInputBorder(),
                    ),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter license plate';
                      }
                      return null;
                    },
                    onChanged: (value) {
                      if (value.length >= 3) {
                        _searchVehicle(value);
                      } else {
                        setState(() {
                          _isSearching = false;
                          _searchResults = [];
                        });
                      }
                    },
                  ),
                ),
                SizedBox(width: 8),
                ElevatedButton.icon(
                  onPressed: _captureLicensePlate,
                  icon: Icon(Icons.camera_alt),
                  label: Text('Scan'),
                  style: ElevatedButton.styleFrom(
                    padding: EdgeInsets.symmetric(vertical: 15),
                  ),
                ),
              ],
            ),
            SizedBox(height: 8),
            ElevatedButton(
              onPressed: () {
                if (_licensePlateController.text.isNotEmpty) {
                  _selectOrCreateVehicle();
                }
              },
              child: Text('Confirm License Plate'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                minimumSize: Size(double.infinity, 45),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSearchResults() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Matching Vehicles',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            _searchResults.isEmpty
              ? Text('No matching vehicles found')
              : ListView.builder(
                  shrinkWrap: true,
                  physics: NeverScrollableScrollPhysics(),
                  itemCount: _searchResults.length,
                  itemBuilder: (context, index) {
                    final vehicle = _searchResults[index];
                    return ListTile(
                      title: Text(vehicle.licensePlate),
                      subtitle: Text(
                        vehicle.companyName ?? 'No company assigned',
                        style: TextStyle(
                          color: vehicle.companyName != null
                            ? Colors.green.shade700
                            : Colors.grey,
                        ),
                      ),
                      trailing: vehicle.isTemporary
                        ? Chip(
                            label: Text('Temporary'),
                            backgroundColor: Colors.orange.shade100,
                          )
                        : null,
                      onTap: () => _selectVehicle(vehicle),
                    );
                  },
                ),
            SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                setState(() {
                  _isNewVehicle = true;
                  _isSearching = false;
                  _selectedVehicle = null;
                  _selectedCompany = null;
                });
              },
              icon: Icon(Icons.add),
              label: Text('Register New Vehicle'),
              style: OutlinedButton.styleFrom(
                minimumSize: Size(double.infinity, 45),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildVehicleDetailsSection() {
    return Card(
      elevation: 2,
      margin: EdgeInsets.symmetric(vertical: 16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Vehicle Details',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 16),
            // Show existing vehicle details or form for new vehicle
            _isNewVehicle
              ? _buildNewVehicleForm()
              : _buildExistingVehicleDetails(),
          ],
        ),
      ),
    );
  }
  
  Widget _buildExistingVehicleDetails() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _infoRow('License Plate', _selectedVehicle!.licensePlate),
        _infoRow('Company', _selectedVehicle!.companyName ?? 'Not assigned'),
        _infoRow('Company Type', _selectedVehicle!.companyType ?? 'Not specified'),
        _infoRow('Vehicle Type', _selectedVehicle!.vehicleType ?? 'Not specified'),
        _infoRow('Registration Date', 
          _selectedVehicle!.registrationDate != null
            ? DateFormat('yyyy-MM-dd').format(_selectedVehicle!.registrationDate!)
            : 'Not available'
        ),
        _infoRow('Status', _selectedVehicle!.isTemporary ? 'Temporary' : 'Regular'),
        
        if (_selectedVehicle!.companyName == null)
          Padding(
            padding: EdgeInsets.only(top: 16),
            child: ElevatedButton.icon(
              onPressed: _navigateToCompanyRegistration,
              icon: Icon(Icons.business),
              label: Text('Register Company for Vehicle'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 45),
              ),
            ),
          ),
      ],
    );
  }
  
  Widget _infoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            flex: 2,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Colors.grey.shade700,
              ),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value,
              style: TextStyle(
                color: label == 'Status' && value == 'Temporary'
                  ? Colors.orange.shade800
                  : null,
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildNewVehicleForm() {
    return Column(
      children: [
        Text(
          'Registering new vehicle: ${_licensePlateController.text.toUpperCase()}',
          style: TextStyle(fontWeight: FontWeight.w500),
        ),
        SizedBox(height: 16),
        
        // Company selection dropdown
        DropdownButtonFormField<String>(
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
            // Set temporary company type
            if (value != null) {
              setState(() {
                _selectedCompany = Company(
                  name: 'New Company',
                  type: value,
                );
              });
            }
          },
          validator: (value) {
            if (value == null) {
              return 'Please select company type';
            }
            return null;
          },
        ),
        SizedBox(height: 16),
        
        // Navigate to complete company registration
        ElevatedButton.icon(
          onPressed: _navigateToCompanyRegistration,
          icon: Icon(Icons.business),
          label: Text('Register Company Details'),
          style: ElevatedButton.styleFrom(
            minimumSize: Size(double.infinity, 45),
          ),
        ),
        
        // Temporary vehicle checkbox
        CheckboxListTile(
          title: Text('Register as temporary vehicle'),
          subtitle: Text('For vehicles that are hired or borrowed'),
          value: true, // New vehicles are temporary by default
          onChanged: (value) {
            // Always temporary for now
          },
          controlAffinity: ListTileControlAffinity.leading,
        ),
      ],
    );
  }
  
  Widget _buildNeighborhoodInput() {
    return Card(
      elevation: 2,
      margin: EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Origin Location',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 8),
            TextFormField(
              controller: _neighborhoodController,
              decoration: InputDecoration(
                labelText: 'Search for neighborhood/area',
                hintText: 'E.g., Kabulonga, Kalingalinga',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.location_on),
              ),
              onChanged: _searchNeighborhoods,
            ),
            
            // Neighborhood search results
            if (_neighborhoodResults.isNotEmpty)
              Container(
                height: 200,
                margin: EdgeInsets.only(top: 8),
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: ListView.builder(
                  itemCount: _neighborhoodResults.length,
                  itemBuilder: (context, index) {
                    final neighborhood = _neighborhoodResults[index];
                    return ListTile(
                      title: Text(neighborhood.name),
                      subtitle: Text(neighborhood.zone ?? 'Unknown zone'),
                      onTap: () {
                        setState(() {
                          _selectedNeighborhood = neighborhood;
                          _neighborhoodController.text = neighborhood.name;
                          _neighborhoodResults = [];
                        });
                      },
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildVehicleImageSection() {
    return Card(
      elevation: 2,
      margin: EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Vehicle Photo',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 16),
            
            // Show image or placeholder
            Center(
              child: _vehicleImage != null
                ? Stack(
                    alignment: Alignment.topRight,
                    children: [
                      Container(
                        height: 200,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          image: DecorationImage(
                            image: FileImage(_vehicleImage!),
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                      IconButton(
                        icon: Icon(Icons.close, color: Colors.white),
                        onPressed: () {
                          setState(() {
                            _vehicleImage = null;
                            _savedImagePath = null;
                          });
                        },
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.black54,
                        ),
                      ),
                    ],
                  )
                : Container(
                    height: 200,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      color: Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.camera_alt, size: 50, color: Colors.grey),
                        SizedBox(height: 8),
                        Text('No image captured', style: TextStyle(color: Colors.grey)),
                      ],
                    ),
                  ),
            ),
            
            SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _captureVehicleImage,
              icon: Icon(Icons.camera_alt),
              label: Text('Capture Vehicle Image'),
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 45),
              ),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildAdditionalInfoSection() {
    return Card(
      elevation: 2,
      margin: EdgeInsets.symmetric(vertical: 8),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Additional Information',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            SizedBox(height: 16),
            
            // Waste type
            TextFormField(
              controller: _wasteTypeController,
              decoration: InputDecoration(
                labelText: 'Waste Type',
                hintText: 'E.g., General, Construction, Garden',
                border: OutlineInputBorder(),
              ),
            ),
            
            SizedBox(height: 16),
            
            // Notes field
            TextFormField(
              controller: _notesController,
              decoration: InputDecoration(
                labelText: 'Notes',
                hintText: 'Any additional information',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
      ),
    );
  }
  
  Future<void> _captureLicensePlate() async {
    setState(() => _isLoading = true);
    
    try {
      final imageFile = await _licensePlateService.takePhoto();
      
      if (imageFile != null) {
        // Also use this as the vehicle image
        setState(() {
          _vehicleImage = imageFile;
        });
        
        // Recognize license plate
        final licensePlate = await _licensePlateService.recognizeLicensePlate(imageFile);
        
        setState(() {
          if (licensePlate != null) {
            _licensePlateController.text = licensePlate;
            _searchVehicle(licensePlate);
          }
        });
      }
    } catch (e) {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
  
  Future<void> _captureVehicleImage() async {
    setState(() => _isLoading = true);
    
    try {
      final imageFile = await _licensePlateService.takePhoto();
      
      if (imageFile != null) {
        setState(() {
          _vehicleImage = imageFile;
        });
      }
    } catch (e) {
      // Show error
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
  
  Future<void> _searchVehicle(String licensePlate) async {
    setState(() {
      _isSearching = true;
      _isLoading = true;
    });
    
    try {
      final offlineSyncService = Provider.of<OfflineSyncService>(context, listen: false);
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      List<Vehicle> results = [];
      
      // Try to search offline first
      final isOnline = await offlineSyncService.isOnline();
      
      if (isOnline) {
        // Online - search in database
        results = await databaseService.searchVehicleByLicensePlate(licensePlate);
        
        // If not found online, search offline
        if (results.isEmpty) {
          results = await offlineSyncService.searchVehiclesOffline(licensePlate);
        }
      } else {
        // Offline - search in Hive
        results = await offlineSyncService.searchVehiclesOffline(licensePlate);
      }
      
      setState(() {
        _searchResults = results;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    }
  }
  
  void _selectVehicle(Vehicle vehicle) {
    setState(() {
      _selectedVehicle = vehicle;
      _licensePlateController.text = vehicle.licensePlate;
      _isSearching = false;
      _isNewVehicle = false;
    });
  }
  
  void _selectOrCreateVehicle() {
    if (_searchResults.isNotEmpty) {
      // Select the first matching vehicle
      _selectVehicle(_searchResults.first);
    } else {
      // Create new vehicle
      setState(() {
        _isNewVehicle = true;
        _isSearching = false;
        _selectedVehicle = null;
        _selectedCompany = null;
      });
    }
  }
  
  Future<void> _searchNeighborhoods(String query) async {
    if (query.length < 2) {
      setState(() {
        _neighborhoodResults = [];
      });
      return;
    }
    
    try {
      final offlineSyncService = Provider.of<OfflineSyncService>(context, listen: false);
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      List<Neighborhood> results = [];
      
      // Try to search offline first
      final isOnline = await offlineSyncService.isOnline();
      
      if (isOnline) {
        // Online - search in database
        results = await databaseService.searchNeighborhoods(query);
        
        // If not found online, search offline
        if (results.isEmpty) {
          results = await offlineSyncService.searchNeighborhoodsOffline(query);
        }
        
        // Cache results offline
        for (final neighborhood in results) {
          await offlineSyncService.saveNeighborhoodOffline(neighborhood);
        }
      } else {
        // Offline - search in Hive
        results = await offlineSyncService.searchNeighborhoodsOffline(query);
      }
      
      setState(() {
        _neighborhoodResults = results;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error searching neighborhoods: ${e.toString()}')),
      );
    }
  }
  
  Future<void> _navigateToCompanyRegistration() async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => CompanyRegistrationScreen(
          initialCompanyType: _selectedCompany?.type ?? 'Franchise',
          vehicleLicensePlate: _licensePlateController.text,
        ),
      ),
    );
    
    if (result != null && result is Company) {
      setState(() {
        _selectedCompany = result;
        
        if (_isNewVehicle) {
          // Create a temporary vehicle linked to this company
          _selectedVehicle = Vehicle(
            licensePlate: _licensePlateController.text.toUpperCase(),
            companyId: result.id,
            companyName: result.name,
            companyType: result.type,
            isTemporary: true,
            registrationDate: DateTime.now(),
          );
          _isNewVehicle = false;
        }
      });
    }
  }
  
  Future<void> _submitEntry() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }
    
    // Ensure we have a vehicle
    if (_selectedVehicle == null && !_isNewVehicle) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please select or register a vehicle')),
      );
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      final offlineSyncService = Provider.of<OfflineSyncService>(context, listen: false);
      final databaseService = Provider.of<DatabaseService>(context, listen: false);
      final isOnline = await offlineSyncService.isOnline();
      
      // Save image if available
      if (_vehicleImage != null) {
        _savedImagePath = await _licensePlateService.saveImage(_vehicleImage!);
      }
      
      // If it's a new vehicle, register it first
      Vehicle vehicleToUse = _selectedVehicle!;
      
      if (_isNewVehicle) {
        // Create a new vehicle
        final newVehicle = Vehicle(
          licensePlate: _licensePlateController.text.toUpperCase(),
          companyId: _selectedCompany?.id,
          vehicleType: 'Garbage Truck', // Default type
          vehicleImageUrl: _savedImagePath,
          isTemporary: true, // New vehicles are temporary by default
          registrationDate: DateTime.now(),
          companyName: _selectedCompany?.name,
          companyType: _selectedCompany?.type,
        );
        
        // Save the vehicle
        if (isOnline) {
          // Online - save to database
          final vehicleId = await databaseService.registerNewVehicle(newVehicle);
          
          if (vehicleId > 0) {
            vehicleToUse = newVehicle.copyWith(id: vehicleId);
          } else {
            throw Exception('Failed to register vehicle');
          }
        } else {
          // Offline - save locally
          await offlineSyncService.saveVehicleOffline(newVehicle);
          vehicleToUse = newVehicle;
        }
      }
      
      // Create visit record
      final record = VisitRecord(
        vehicleId: vehicleToUse.id ?? -1,
        entryTime: DateTime.now(),
        neighborhoodId: _selectedNeighborhood?.id,
        wasteType: _wasteTypeController.text,
        notes: _notesController.text,
        createdBy: 'User', // Replace with actual user info
        imageUrl: _savedImagePath,
        offlineCreated: !isOnline,
        licensePlate: vehicleToUse.licensePlate,
        companyName: vehicleToUse.companyName,
        neighborhoodName: _selectedNeighborhood?.name,
      );
      
      // Save the record
      if (isOnline) {
        // Online - save to database
        final recordId = await databaseService.saveVisitRecord(record);
        
        if (recordId <= 0) {
          throw Exception('Failed to save visit record');
        }
      } else {
        // Offline - save locally
        await offlineSyncService.saveVisitRecordOffline(record);
      }
      
      // Reset form
      setState(() {
        _licensePlateController.clear();
        _neighborhoodController.clear();
        _wasteTypeController.clear();
        _notesController.clear();
        _selectedVehicle = null;
        _selectedCompany = null;
        _selectedNeighborhood = null;
        _vehicleImage = null;
        _savedImagePath = null;
        _isNewVehicle = false;
        _isSearching = false;
        _searchResults = [];
        _neighborhoodResults = [];
      });
      
      // Show success message
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Vehicle entry recorded successfully'),
          backgroundColor: Colors.green,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }
}

// Extension for copying
extension VehicleCopyWith on Vehicle {
  Vehicle copyWith({
    int? id,
    String? licensePlate,
    int? companyId,
    String? vehicleType,
    String? vehicleImageUrl,
    DateTime? registrationDate,
    bool? isTemporary,
    DateTime? tempExpiryDate,
    DateTime? lastVisitDate,
    String? companyName,
    String? companyType,
  }) {
    return Vehicle(
      id: id ?? this.id,
      licensePlate: licensePlate ?? this.licensePlate,
      companyId: companyId ?? this.companyId,
      vehicleType: vehicleType ?? this.vehicleType,
      vehicleImageUrl: vehicleImageUrl ?? this.vehicleImageUrl,
      registrationDate: registrationDate ?? this.registrationDate,
      isTemporary: isTemporary ?? this.isTemporary,
      tempExpiryDate: tempExpiryDate ?? this.tempExpiryDate,
      lastVisitDate: lastVisitDate ?? this.lastVisitDate,
      companyName: companyName ?? this.companyName,
      companyType: companyType ?? this.companyType,
    );
  }
}