#!/bin/bash

set -e

echo "🚀 Setting up Trading System..."

# Check if we're in the right directory
if [ ! -f "backend/core/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/trading
mkdir -p config

# Setup Python environment
echo "🐍 Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install requirements
echo "📦 Installing Python requirements..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# Setup environment file
echo "⚙️ Setting up environment configuration..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env from template"
    echo "⚠️  Please edit backend/.env with your actual API credentials"
else
    echo "ℹ️  backend/.env already exists"
fi

# Check for Docker and Docker Compose
echo "🐳 Checking Docker setup..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker and Docker Compose are available"
    
    # Start infrastructure services
    echo "🔧 Starting infrastructure services..."
    docker-compose up -d clickhouse redis
    
    # Wait for services to be ready
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    # Run database migrations
    echo "🗄️ Running database migrations..."
    docker exec trading_clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS bitget"
    
    if [ -f "backend/db/migrations/20250113_add_trading_tables.sql" ]; then
        docker exec -i trading_clickhouse clickhouse-client --database=bitget < backend/db/migrations/20250113_add_trading_tables.sql
        echo "✅ Database migrations completed"
    fi
    
else
    echo "⚠️  Docker not found. Please install Docker and Docker Compose"
    echo "   You can still run the system with external ClickHouse and Redis"
fi

# Create startup script
echo "📝 Creating startup script..."
cat > start_trading_api.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Trading API..."

# Activate virtual environment
source venv/bin/activate

# Start the API
cd backend
uvicorn core.main:app --host 0.0.0.0 --port 8000 --reload

EOF

chmod +x start_trading_api.sh

# Create test script
echo "🧪 Creating test script..."
cat > test_trading_api.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing Trading API..."

# Wait for API to be ready
sleep 2

# Test health endpoint
echo "Testing health endpoint..."
curl -s http://localhost:8000/trading/health | python -m json.tool

echo ""
echo "Testing root endpoint..."
curl -s http://localhost:8000/ | python -m json.tool

echo ""
echo "✅ Basic API tests completed"
echo "📖 Full API documentation available at: http://localhost:8000/docs"

EOF

chmod +x test_trading_api.sh

echo ""
echo "🎉 Trading System setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Edit backend/.env with your API credentials"
echo "2. Start the API: ./start_trading_api.sh"
echo "3. Test the API: ./test_trading_api.sh"
echo "4. View API docs: http://localhost:8000/docs"
echo ""
echo "🔗 Available endpoints:"
echo "   - Trading Health: http://localhost:8000/trading/health"
echo "   - API Documentation: http://localhost:8000/docs"
echo "   - Grid Calculator: http://localhost:8000/trading/grid/calculate-levels"
echo ""
echo "⚠️  Remember to:"
echo "   - Configure your Bitget API credentials in backend/.env"
echo "   - Set TRADING_ENABLED=true when ready for live trading"
echo "   - Start with BITGET_SANDBOX=true for testing"
