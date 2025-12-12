# Clone the repository
git clone https://gitlab.remzona.dev/tools/python/notifyopenprj_telergrambot

cd {project_directory}

# Create virtual environment
python3 -m venv venv

source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file with your configuration

# Run the application
python run.py