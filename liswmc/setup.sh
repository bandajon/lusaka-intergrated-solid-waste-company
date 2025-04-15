#!/bin/bash
# Setup script for LISWMC Dumpsite Tracker app

set -e # Exit on any error

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Temporary directory for downloads
TEMP_DIR="$HOME/flutter_setup_temp"
mkdir -p "$TEMP_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LISWMC Dumpsite Tracker Setup Script  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}This script will help you set up Flutter and the necessary tools for the app.${NC}"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to add to PATH in the appropriate shell config file
add_to_path() {
    local path_to_add=$1
    local shell_file=""
    
    # Determine shell config file
    if [[ -n "$ZSH_VERSION" ]]; then
        shell_file="$HOME/.zshrc"
    elif [[ -n "$BASH_VERSION" ]]; then
        shell_file="$HOME/.bashrc"
        # For macOS, also update .bash_profile if it exists
        if [[ "$OS" == "macos" && -f "$HOME/.bash_profile" ]]; then
            echo "export PATH=\"$path_to_add:\$PATH\"" >> "$HOME/.bash_profile"
        fi
    else
        # Default to .profile
        shell_file="$HOME/.profile"
    fi
    
    # Add to PATH if not already in it
    if ! grep -q "$path_to_add" "$shell_file" 2>/dev/null; then
        echo "export PATH=\"$path_to_add:\$PATH\"" >> "$shell_file"
        echo -e "${GREEN}Added Flutter to PATH in $shell_file${NC}"
    else
        echo -e "${YELLOW}Flutter already in PATH in $shell_file${NC}"
    fi
}

# Step 1: Install Flutter SDK
install_flutter() {
    echo -e "\n${BLUE}[Step 1/5] Installing Flutter SDK${NC}"
    
    # Check if Flutter is already installed
    if command_exists flutter; then
        FLUTTER_VERSION=$(flutter --version | head -n 1)
        echo -e "${YELLOW}Flutter is already installed:${NC}"
        echo -e "${YELLOW}$FLUTTER_VERSION${NC}"
        read -p "Do you want to reinstall Flutter? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    FLUTTER_INSTALL_DIR="$HOME/flutter"
    
    # Use Git to directly clone the latest stable Flutter SDK
    echo "Downloading the latest Flutter SDK using Git..."
    
    # Clone Flutter repository directly (this ensures latest stable version)
    cd "$HOME" && git clone https://github.com/flutter/flutter.git -b stable
    
    if [ -d "$HOME/flutter" ]; then
        echo -e "${GREEN}Successfully downloaded the latest Flutter SDK${NC}"
        SKIP_EXTRACTION=true
    else
        echo -e "${RED}Failed to download Flutter. Please install manually from https://flutter.dev/docs/get-started/install${NC}"
        exit 1
    fi
    
    # Remove existing installation if present and we're not using git clone directly
    if [ -d "$FLUTTER_INSTALL_DIR" ] && [ "${SKIP_EXTRACTION:-false}" != "true" ]; then
        echo "Removing existing Flutter installation..."
        rm -rf "$FLUTTER_INSTALL_DIR"
    fi
    
    # Extract Flutter SDK if needed
    if [ "${SKIP_EXTRACTION:-false}" != "true" ]; then
        echo "Extracting Flutter SDK..."
        if [[ "$OS" == "linux" ]]; then
            tar xf "$TEMP_DIR/flutter.zip" -C "$HOME" || {
                echo -e "${RED}Failed to extract Flutter SDK. Trying alternative method...${NC}"
                cd "$HOME" && git clone https://github.com/flutter/flutter.git -b stable
            }
        else
            unzip -q "$TEMP_DIR/flutter.zip" -d "$HOME" || {
                echo -e "${RED}Failed to extract Flutter SDK. Trying alternative method...${NC}"
                cd "$HOME" && git clone https://github.com/flutter/flutter.git -b stable
            }
        fi
    else
        echo "Skipping extraction as Flutter was downloaded via git."
    fi
    
    # Add Flutter to PATH
    add_to_path "$FLUTTER_INSTALL_DIR/bin"
    
    # Set PATH for current session
    export PATH="$FLUTTER_INSTALL_DIR/bin:$PATH"
    
    echo -e "${GREEN}Flutter SDK installed successfully at $FLUTTER_INSTALL_DIR${NC}"
}

# Step 2: Install Flutter dependencies
install_dependencies() {
    echo -e "\n${BLUE}[Step 2/5] Installing Flutter dependencies${NC}"
    
    # Run Flutter doctor to check dependencies
    flutter doctor
    
    # Install platform-specific dependencies
    case $OS in
        macos)
            # Check if Homebrew is installed
            if ! command_exists brew; then
                echo "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            # Install CocoaPods for iOS development
            if ! command_exists pod; then
                echo "Installing CocoaPods..."
                sudo gem install cocoapods
            fi
            
            # Install Android Studio if needed
            read -p "Do you want to install Android Studio? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                brew install --cask android-studio
            fi
            ;;
        linux)
            # Install Linux dependencies
            echo "Installing Linux dependencies..."
            sudo apt-get update
            sudo apt-get install -y curl git unzip xz-utils zip libglu1-mesa
            
            # For Android development
            read -p "Do you want to install Android Studio? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "Please visit https://developer.android.com/studio to download and install Android Studio."
            fi
            ;;
        windows)
            echo "Please make sure you have Git installed."
            echo "To install Android Studio, visit https://developer.android.com/studio"
            ;;
    esac
    
    echo -e "${GREEN}Dependencies set up. You may need to complete some manual steps as indicated above.${NC}"
}

# Step 3: Configure Flutter
configure_flutter() {
    echo -e "\n${BLUE}[Step 3/5] Configuring Flutter${NC}"
    
    # Upgrade Flutter to the latest version
    echo "Upgrading Flutter to the latest version..."
    flutter upgrade
    
    # Run Flutter doctor to check status
    flutter doctor -v
    
    # Accept Android licenses
    flutter doctor --android-licenses || true
    
    # Enable web support and other features
    flutter config --enable-web
    flutter config --enable-macos-desktop
    flutter config --enable-ios
    flutter config --enable-android
    
    # Update Flutter again to ensure everything is up to date
    flutter upgrade
    
    echo -e "${GREEN}Flutter configured successfully with the latest version${NC}"
}

# Step 4: Set up the project
setup_project() {
    echo -e "\n${BLUE}[Step 4/5] Setting up the project${NC}"
    
    # Navigate to the project directory
    cd "$(dirname "$0")/dumpsite_tracker"
    
    # Get dependencies
    echo "Fetching Flutter dependencies..."
    flutter pub get
    
    # Update flutter_tools dependency for null safety
    echo "Updating flutter_tools dependency..."
    cd "$HOME/flutter/packages/flutter_tools" && dart pub get
    
    # Generate code
    echo "Generating code..."
    cd "$(dirname "$0")/dumpsite_tracker" && flutter pub run build_runner build --delete-conflicting-outputs || true
    
    echo -e "${GREEN}Project set up successfully${NC}"
}

# Step 5: Run the app
run_app() {
    echo -e "\n${BLUE}[Step 5/5] Running the app${NC}"
    
    # Navigate to the project directory
    cd "$(dirname "$0")/dumpsite_tracker"
    
    # Check available devices
    echo "Checking available devices..."
    flutter devices
    
    # Prompt to run
    read -p "Do you want to run the app now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Run the app
        flutter run
    else
        echo -e "${YELLOW}You can run the app later with 'flutter run' from the project directory.${NC}"
    fi
}

# Main execution
install_flutter
install_dependencies
configure_flutter
setup_project
run_app

# Clean up
rm -rf "$TEMP_DIR"

echo -e "\n${GREEN}Setup completed successfully!${NC}"
echo -e "${YELLOW}Remember to complete the Firebase configuration in:${NC}"
echo -e "${YELLOW}lib/config/firebase_options.dart${NC}"
echo -e "\n${BLUE}To run the app again, navigate to the project directory and run:${NC}"
echo -e "${BLUE}cd $(dirname "$0")/dumpsite_tracker${NC}"
echo -e "${BLUE}flutter run${NC}"