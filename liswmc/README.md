# LISWMC Dumpsite Tracker

A Flutter application for tracking vehicles entering the Lusaka Integrated Solid Waste Management Company dumpsites.

## Features

- License plate recognition using ML Kit OCR
- Vehicle photo capture and storage
- Company registration and management
- Offline capabilities with Hive database
- Firebase authentication
- PostgreSQL database integration
- Classification of waste management companies (Franchise, Community, LISWMC, Private)

## Installation

### Automated Setup (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lusaka-intergrated-solid-waste-management-company/liswmc
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```
   
   This script will:
   - Install Flutter SDK
   - Set up required dependencies
   - Configure Flutter
   - Set up the project
   - Run the app

### Manual Setup

1. Install Flutter by following the instructions at [flutter.dev](https://flutter.dev/docs/get-started/install)

2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lusaka-intergrated-solid-waste-management-company/liswmc/dumpsite_tracker
   ```

3. Get dependencies:
   ```bash
   flutter pub get
   ```

4. Generate necessary code:
   ```bash
   flutter pub run build_runner build --delete-conflicting-outputs
   ```

5. Run the app:
   ```bash
   flutter run
   ```

## Firebase Configuration

Before running the app, you need to configure Firebase:

1. Create a Firebase project at [firebase.google.com](https://console.firebase.google.com/)

2. Add your Android and iOS apps to the Firebase project

3. Update the Firebase configuration in:
   ```
   lib/config/firebase_options.dart
   ```

## Database Configuration

The app is configured to use PostgreSQL with the following connection string:
```
postgresql://agripredict:Wee8fdm0k2!!@agripredict-prime-prod.caraj6fzskso.eu-west-2.rds.amazonaws.com:5432/users
```

## App Structure

- **lib/models/** - Data models (Vehicle, Company, Visit Record, etc.)
- **lib/screens/** - UI screens
- **lib/services/** - Business logic (Authentication, Database, License Plate Recognition, etc.)
- **lib/config/** - Configuration files
- **lib/widgets/** - Reusable UI components

## Key Screens

1. **Login Screen** - Authentication with offline capability
2. **Vehicle Entry Screen** - Record vehicles entering the dumpsite
3. **Company Registration** - Register new waste management companies
4. **History** - View previous entries

## Usage

1. Log in with Firebase credentials or use offline login
2. Use the camera to scan license plates
3. Register new companies and vehicles as needed
4. Record vehicle entries with waste type and origin location
5. Data synchronizes automatically when online

## Offline Functionality

The app includes robust offline capabilities:
- Offline authentication
- Local storage of vehicle and company data
- Queued synchronization when connectivity is restored
- Image storage and processing

## Development

### Running Tests

```bash
flutter test
```

### Building for Production

```bash
flutter build apk --release  # Android
flutter build ios --release  # iOS (requires macOS)
```

## License

[Specify your license]

## Contact

For support or inquiries, contact: [Your contact information]