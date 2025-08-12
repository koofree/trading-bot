#!/bin/bash

# Install dependencies for different operating systems

echo "📦 Installing Trading Bot Dependencies"
echo "======================================"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/debian_version ]; then
        OS="debian"
    elif [ -f /etc/redhat-release ]; then
        OS="redhat"
    else
        OS="linux"
    fi
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# macOS Installation
if [ "$OS" == "macos" ]; then
    echo "Installing dependencies for macOS..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Update Homebrew
    brew update
    
    # Install PostgreSQL
    echo "Installing PostgreSQL..."
    brew install postgresql@15
    brew services start postgresql@15
    
    # Install Redis
    echo "Installing Redis..."
    brew install redis
    brew services start redis
    
    # Install Python 3.10
    echo "Installing Python 3.10..."
    brew install python@3.10
    
    # Install Node.js
    echo "Installing Node.js..."
    brew install node
    
    # Install additional tools
    brew install git wget curl
    
    echo "✅ macOS dependencies installed!"
    echo "Services started: PostgreSQL, Redis"
fi

# Debian/Ubuntu Installation
if [ "$OS" == "debian" ]; then
    echo "Installing dependencies for Debian/Ubuntu..."
    
    # Update package list
    sudo apt update
    
    # Install PostgreSQL
    echo "Installing PostgreSQL..."
    sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    sudo apt update
    sudo apt install -y postgresql-15 postgresql-client-15
    
    # Start PostgreSQL
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Install Redis
    echo "Installing Redis..."
    sudo apt install -y redis-server
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Install Python 3.10
    echo "Installing Python 3.10..."
    sudo apt install -y python3.10 python3.10-venv python3-pip
    
    # Install Node.js 18
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    # Install additional tools
    sudo apt install -y git curl wget build-essential
    
    echo "✅ Debian/Ubuntu dependencies installed!"
    echo "Services started: PostgreSQL, Redis"
fi

# Red Hat/CentOS/Fedora Installation
if [ "$OS" == "redhat" ]; then
    echo "Installing dependencies for Red Hat/CentOS/Fedora..."
    
    # Install PostgreSQL
    echo "Installing PostgreSQL..."
    sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
    sudo yum install -y postgresql15 postgresql15-server
    sudo /usr/pgsql-15/bin/postgresql-15-setup initdb
    sudo systemctl enable postgresql-15
    sudo systemctl start postgresql-15
    
    # Install Redis
    echo "Installing Redis..."
    sudo yum install -y epel-release
    sudo yum install -y redis
    sudo systemctl start redis
    sudo systemctl enable redis
    
    # Install Python 3.10
    echo "Installing Python 3.10..."
    sudo yum install -y python3 python3-pip python3-devel
    
    # Install Node.js
    echo "Installing Node.js..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo yum install -y nodejs
    
    # Install additional tools
    sudo yum install -y git wget curl gcc gcc-c++ make
    
    echo "✅ Red Hat/CentOS/Fedora dependencies installed!"
    echo "Services started: PostgreSQL, Redis"
fi

# Create PostgreSQL user and database
echo ""
echo "Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
CREATE USER trading_user WITH PASSWORD 'trading_password';
CREATE DATABASE trading_bot OWNER trading_user;
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_user;
EOF

echo "✅ Database 'trading_bot' created with user 'trading_user'"

# Verify installations
echo ""
echo "Verifying installations..."
echo "=========================="

# Check Python
python3 --version
if [ $? -eq 0 ]; then
    echo "✅ Python installed"
else
    echo "❌ Python installation failed"
fi

# Check Node.js
node --version
if [ $? -eq 0 ]; then
    echo "✅ Node.js installed"
else
    echo "❌ Node.js installation failed"
fi

# Check PostgreSQL
psql --version
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL installed"
else
    echo "❌ PostgreSQL installation failed"
fi

# Check Redis
redis-cli --version
if [ $? -eq 0 ]; then
    echo "✅ Redis installed"
else
    echo "❌ Redis installation failed"
fi

echo ""
echo "Installation complete! Next steps:"
echo "1. Run ./setup.sh to set up the project"
echo "2. Edit .env file with your API keys"
echo "3. Start the application"