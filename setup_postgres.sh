#!/bin/bash
# Script to help set up PostgreSQL for the website monitoring system

# Display colorful text
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}  SiteSentinel PostgreSQL Setup Helper${NC}"
echo -e "${BLUE}====================================================${NC}"

# Check if PostgreSQL is installed
if command -v psql >/dev/null 2>&1; then
    echo -e "${GREEN}PostgreSQL is installed.${NC}"
else
    echo -e "${RED}PostgreSQL is not installed!${NC}"
    echo -e "${YELLOW}Please install PostgreSQL using one of the following commands:${NC}"
    echo -e "  Ubuntu/Debian: ${GREEN}sudo apt update && sudo apt install postgresql postgresql-contrib${NC}"
    echo -e "  Fedora/RHEL/CentOS: ${GREEN}sudo dnf install postgresql postgresql-server${NC}"
    echo -e "  macOS (with Homebrew): ${GREEN}brew install postgresql${NC}"
    echo -e "After installation, come back and run this script again."
    exit 1
fi

# Check if PostgreSQL service is running
if systemctl is-active --quiet postgresql 2>/dev/null || pgrep -x postgres >/dev/null || pgrep -x postmaster >/dev/null; then
    echo -e "${GREEN}PostgreSQL service is running.${NC}"
else
    echo -e "${YELLOW}PostgreSQL service doesn't seem to be running.${NC}"
    echo -e "Attempting to start PostgreSQL service..."
    sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null
    
    # Check again if the service started
    if systemctl is-active --quiet postgresql 2>/dev/null || pgrep -x postgres >/dev/null || pgrep -x postmaster >/dev/null; then
        echo -e "${GREEN}PostgreSQL service started successfully.${NC}"
    else
        echo -e "${RED}Failed to start PostgreSQL service.${NC}"
        echo -e "Please start it manually using one of these commands:"
        echo -e "  ${GREEN}sudo systemctl start postgresql${NC}"
        echo -e "  ${GREEN}sudo service postgresql start${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}---------------------------------------------------${NC}"
echo -e "${YELLOW}Would you like to set up the database with default credentials?${NC}"
echo -e "This will:"
echo -e "1. Create a PostgreSQL user 'postgres' with password 'postgres'"
echo -e "2. Create a database 'sitesentinel'"
echo -e "3. Configure the application to use these credentials"
echo -e ""
read -p "Proceed? (y/n): " answer

if [[ $answer != "y" && $answer != "Y" ]]; then
    echo -e "${YELLOW}Setup cancelled. You can manually configure the database settings in config.json${NC}"
    exit 0
fi

# Check if postgres user exists
if sudo -u postgres psql -c "\du" | grep -q postgres; then
    echo -e "${GREEN}User 'postgres' already exists.${NC}"
else
    echo -e "${YELLOW}Creating PostgreSQL user 'postgres'...${NC}"
    sudo -u postgres createuser -s -i -d -r -l -w postgres
    echo -e "${GREEN}User created successfully.${NC}"
fi

# Set postgres user password
echo -e "${YELLOW}Setting password for 'postgres' user...${NC}"
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'postgres';"
echo -e "${GREEN}Password set successfully.${NC}"

# Create the database
echo -e "${YELLOW}Creating 'sitesentinel' database...${NC}"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw sitesentinel; then
    echo -e "${GREEN}Database 'sitesentinel' already exists.${NC}"
else
    sudo -u postgres createdb sitesentinel
    echo -e "${GREEN}Database created successfully.${NC}"
fi

# Verify the connection works
echo -e "${YELLOW}Verifying database connection...${NC}"
if PGPASSWORD=postgres psql -h localhost -U postgres -d sitesentinel -c "SELECT 1" > /dev/null 2>&1; then
    echo -e "${GREEN}Database connection successful!${NC}"
else
    echo -e "${RED}Could not connect to the database.${NC}"
    echo -e "${YELLOW}Please check your PostgreSQL configuration.${NC}"
    echo -e "You may need to modify the pg_hba.conf file to allow password authentication."
    exit 1
fi

echo -e "${BLUE}---------------------------------------------------${NC}"
echo -e "${GREEN}PostgreSQL setup completed successfully!${NC}"
echo -e ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Run the Python setup script: ${GREEN}python setup_db.py${NC}"
echo -e "2. Start the application: ${GREEN}python src/main.py${NC}"
echo -e "${BLUE}====================================================${NC}"