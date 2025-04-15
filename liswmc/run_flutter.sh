#!/bin/bash
# This script temporarily adds Flutter to your PATH and runs the specified Flutter command

# Add Flutter to PATH for this script
export PATH="$HOME/flutter/bin:$PATH"

# Display the Flutter version
echo "Flutter version:"
flutter --version
echo ""

# Check if a command was provided
if [ $# -eq 0 ]; then
  echo "No command specified. Available commands:"
  echo "  flutter doctor    - Check Flutter setup"
  echo "  flutter pub get   - Get dependencies"
  echo "  flutter run       - Run the app"
  echo "  flutter build     - Build the app"
  echo "  flutter upgrade   - Upgrade Flutter"
  echo ""
  echo "Usage: ./run_flutter.sh <flutter_command>"
  echo "Example: ./run_flutter.sh 'flutter doctor'"
  echo ""
  
  # Always provide an overview of the Flutter setup
  echo "Running 'flutter doctor' to show the state of your Flutter installation:"
  flutter doctor
else
  # Execute the provided command
  echo "Running command: $@"
  $@
fi

echo ""
echo "To permanently add Flutter to your PATH, run the following command:"
echo "echo 'export PATH=\"\$HOME/flutter/bin:\$PATH\"' >> ~/.zshrc && source ~/.zshrc"