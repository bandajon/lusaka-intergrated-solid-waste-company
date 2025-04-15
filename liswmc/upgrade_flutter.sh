#!/bin/bash
# Script to install/upgrade Flutter to the latest stable version

set -e # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Flutter Installation/Upgrade Script ${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Flutter already exists
if [ -d "$HOME/flutter" ]; then
    echo -e "${YELLOW}Existing Flutter installation found.${NC}"
    read -p "Do you want to completely reinstall Flutter? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating backup of existing Flutter installation..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mkdir -p "$HOME/flutter_backups"
        if [ -d "$HOME/flutter" ]; then
            mv "$HOME/flutter" "$HOME/flutter_backups/flutter_$TIMESTAMP"
            echo -e "${GREEN}Backup created at $HOME/flutter_backups/flutter_$TIMESTAMP${NC}"
        fi
        
        # Clean install
        echo "Removing previous installation..."
        rm -rf "$HOME/flutter"
    else
        echo "Will attempt to upgrade the existing installation."
        echo "Note: This might fail if your Flutter installation has local changes."
        
        # Try to upgrade existing installation
        cd "$HOME/flutter"
        
        # Reset any local changes
        echo "Resetting local changes..."
        git reset --hard HEAD
        
        # Make sure we're on the stable branch
        echo "Switching to stable branch..."
        git checkout stable
        
        # Pull latest changes
        echo "Pulling latest changes..."
        git pull origin stable
        
        # Update Flutter
        echo "Upgrading Flutter..."
        "$HOME/flutter/bin/flutter" upgrade
        
        echo -e "${GREEN}Flutter has been upgraded to the latest stable version.${NC}"
        "$HOME/flutter/bin/flutter" --version
        
        # Add Flutter to PATH if not already there
        if ! grep -q "flutter/bin" "$HOME/.zshrc" 2>/dev/null && ! grep -q "flutter/bin" "$HOME/.bashrc" 2>/dev/null; then
            echo "Adding Flutter to your PATH..."
            if [ -f "$HOME/.zshrc" ]; then
                echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.zshrc"
                echo -e "${GREEN}Added Flutter to PATH in .zshrc${NC}"
            elif [ -f "$HOME/.bashrc" ]; then
                echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.bashrc"
                echo -e "${GREEN}Added Flutter to PATH in .bashrc${NC}"
            else
                echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.profile"
                echo -e "${GREEN}Added Flutter to PATH in .profile${NC}"
            fi
        fi
        
        # Exit early as we've successfully upgraded
        exit 0
    fi
fi

# Fresh installation if we get here
echo "Installing Flutter from scratch..."

# Clone Flutter repository
echo "Cloning the Flutter repository..."
git clone https://github.com/flutter/flutter.git -b stable "$HOME/flutter"

# Add Flutter to PATH
if ! grep -q "flutter/bin" "$HOME/.zshrc" 2>/dev/null && ! grep -q "flutter/bin" "$HOME/.bashrc" 2>/dev/null; then
    echo "Adding Flutter to your PATH..."
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.zshrc"
        echo -e "${GREEN}Added Flutter to PATH in .zshrc${NC}"
    elif [ -f "$HOME/.bashrc" ]; then
        echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.bashrc"
        echo -e "${GREEN}Added Flutter to PATH in .bashrc${NC}"
    else
        echo 'export PATH="$HOME/flutter/bin:$PATH"' >> "$HOME/.profile"
        echo -e "${GREEN}Added Flutter to PATH in .profile${NC}"
    fi
fi

# Set PATH for current session
export PATH="$HOME/flutter/bin:$PATH"

# Run Flutter commands
echo "Checking Flutter version..."
"$HOME/flutter/bin/flutter" --version

echo "Running Flutter doctor..."
"$HOME/flutter/bin/flutter" doctor

echo "Configuring Flutter..."
"$HOME/flutter/bin/flutter" config --enable-web
"$HOME/flutter/bin/flutter" config --enable-macos-desktop
"$HOME/flutter/bin/flutter" config --enable-ios
"$HOME/flutter/bin/flutter" config --enable-android

echo -e "${GREEN}Flutter has been successfully installed!${NC}"
echo -e "${YELLOW}Note: You may need to restart your terminal or run 'source ~/.zshrc' (or ~/.bashrc) to update your PATH.${NC}"
echo -e "${YELLOW}Try running 'flutter --version' to confirm the installation.${NC}"

# Return to the project directory if it exists
if [ -d "/Users/admin/lusaka-intergrated-solid-waste-management-company/liswmc/dumpsite_tracker" ]; then
    echo -e "\n${BLUE}Setting up the project...${NC}"
    cd "/Users/admin/lusaka-intergrated-solid-waste-management-company/liswmc/dumpsite_tracker"
    
    # Ask if user wants to set up the project
    read -p "Do you want to set up the project (get dependencies)? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Getting Flutter dependencies..."
        "$HOME/flutter/bin/flutter" pub get
        
        echo "Running Flutter doctor again to check project setup..."
        "$HOME/flutter/bin/flutter" doctor
        
        echo -e "${GREEN}Project dependencies have been installed.${NC}"
        echo -e "${YELLOW}You can now run the app with 'flutter run'${NC}"
    fi
fi