#!/bin/bash

# Authentication Fix Script for Azure Advisor Reports Platform
# Version: 1.2.2
# Purpose: Clean cache and rebuild frontend to fix authentication issues

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}Azure Advisor Reports - Authentication Fix${NC}"
echo -e "${CYAN}Version 1.2.2${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Check if we're in the correct directory
if [ ! -f "frontend/package.json" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    echo -e "${YELLOW}Current directory: $(pwd)${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6] Checking environment variables...${NC}"

# Check if .env.local exists
if [ ! -f "frontend/.env.local" ]; then
    echo -e "${RED}  Warning: frontend/.env.local not found!${NC}"
    echo -e "${YELLOW}  Creating from .env.example...${NC}"
    cp "frontend/.env.example" "frontend/.env.local"
    echo -e "${YELLOW}  Please edit frontend/.env.local with your Azure AD credentials${NC}"

    # Open in default editor
    ${EDITOR:-nano} "frontend/.env.local"

    echo ""
    read -p "Press Enter after saving the file..."
fi

# Verify required variables
required_vars=("REACT_APP_AZURE_CLIENT_ID" "REACT_APP_AZURE_TENANT_ID" "REACT_APP_AZURE_REDIRECT_URI")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=.\\+" "frontend/.env.local"; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    echo -e "${RED}  Error: Missing required environment variables:${NC}"
    for var in "${missing_vars[@]}"; do
        echo -e "${RED}    - $var${NC}"
    done
    echo -e "${YELLOW}  Please update frontend/.env.local and run this script again${NC}"
    exit 1
fi

echo -e "${GREEN}  Environment variables configured${NC}"
echo ""

echo -e "${YELLOW}[2/6] Stopping running processes...${NC}"

# Stop any running node processes on port 3000
if lsof -ti:3000 >/dev/null 2>&1; then
    echo -e "${GRAY}  Stopping process on port 3000${NC}"
    kill -9 $(lsof -ti:3000) 2>/dev/null || true
    sleep 2
fi

echo -e "${GREEN}  Processes stopped${NC}"
echo ""

echo -e "${YELLOW}[3/6] Cleaning frontend cache...${NC}"

# Clean frontend build directories
dirs_to_clean=(
    "frontend/build"
    "frontend/node_modules/.cache"
    "frontend/.cache"
)

for dir in "${dirs_to_clean[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GRAY}  Removing $dir${NC}"
        rm -rf "$dir"
    fi
done

echo -e "${GREEN}  Frontend cache cleaned${NC}"
echo ""

echo -e "${YELLOW}[4/6] Cleaning npm cache...${NC}"

cd frontend
npm cache clean --force >/dev/null 2>&1
echo -e "${GREEN}  NPM cache cleaned${NC}"
cd ..
echo ""

echo -e "${YELLOW}[5/6] Reinstalling dependencies...${NC}"

# Option to skip node_modules reinstall
read -p "Do you want to reinstall node_modules? This may take a few minutes. (y/N): " reinstall

if [[ "$reinstall" =~ ^[Yy]$ ]]; then
    cd frontend

    if [ -d "node_modules" ]; then
        echo -e "${GRAY}  Removing node_modules...${NC}"
        rm -rf "node_modules"
    fi

    echo -e "${GRAY}  Installing dependencies (this may take a while)...${NC}"
    npm install

    cd ..
    echo -e "${GREEN}  Dependencies installed${NC}"
else
    echo -e "${YELLOW}  Skipping node_modules reinstall${NC}"
fi
echo ""

echo -e "${YELLOW}[6/6] Verifying configuration...${NC}"

# Read and display current configuration (obfuscated)
while IFS= read -r line; do
    if [[ $line =~ ^REACT_APP_AZURE_(CLIENT_ID|TENANT_ID)=(.+) ]]; then
        var_name="${BASH_REMATCH[1]}"
        var_value="${BASH_REMATCH[2]}"
        if [ ${#var_value} -gt 8 ]; then
            obfuscated="${var_value:0:8}..."
            echo -e "${GRAY}  $var_name = $obfuscated${NC}"
        fi
    fi
done < "frontend/.env.local"

echo -e "${GREEN}  Configuration verified${NC}"
echo ""

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}Authentication fix completed successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

echo -e "${CYAN}Next steps:${NC}"
echo -e "${NC}1. Start the backend server:${NC}"
echo -e "${GRAY}   cd azure_advisor_reports${NC}"
echo -e "${GRAY}   python manage.py runserver${NC}"
echo ""
echo -e "${NC}2. Start the frontend server:${NC}"
echo -e "${GRAY}   cd frontend${NC}"
echo -e "${GRAY}   npm start${NC}"
echo ""
echo -e "${NC}3. If you still have authentication issues:${NC}"
echo -e "${GRAY}   - Open http://localhost:3000/clear-auth-cache.html${NC}"
echo -e "${GRAY}   - Click 'Clear All Authentication Cache'${NC}"
echo -e "${GRAY}   - Return to the app and try logging in again${NC}"
echo ""

read -p "Do you want to start the frontend server now? (y/N): " start_now

if [[ "$start_now" =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${CYAN}Starting frontend server...${NC}"
    echo -e "${YELLOW}Note: Press Ctrl+C to stop the server${NC}"
    echo ""

    cd frontend
    npm start
    cd ..
else
    echo ""
    echo -e "${NC}You can start the servers manually when ready.${NC}"
    echo ""
fi
