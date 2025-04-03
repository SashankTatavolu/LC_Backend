# Lnaguage Communicator Backend

## Overview
This backend powers the multi-layered validation tool designed for correcting Universal Semantic Representation (USR) information. It processes uploaded data, separates different USR components, supports manual corrections, and integrates AI-driven modules for validation, text generation, and visualization.

## Features
- **USR Processing:** Automatically separates lexical, construction, relational, discourse, and coreference information.
- **Manual Correction Support:** Enables annotators to refine USRs.
- **Hindi Text Generator:** Converts USRs into Hindi text.
- **Visualization Module:** Displays concept interrelations using Graphviz and Digraph.
- **API-Based Communication:** Provides RESTful endpoints for interaction with the frontend.
- **Optimized Performance:** Utilizes Redis caching and PostgreSQL for efficient storage.

## Technology Stack
- **Framework:** Flask (Python)
- **Database:** PostgreSQL
- **Cache Layer:** Redis
- **Libraries & Tools:**
  - Flask-RESTful for API endpoints
  - SQLAlchemy for database management
  - Graphviz and Digraph for visualization
  - IndicNLP/iNLTK for Hindi text generation

## Installation & Setup
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- PostgreSQL
- Redis

### Steps to Install & Run
1. **Clone the Repository:**
   ```sh
   git clone <repository_url>
   cd backend
   ```
2. **Create a Virtual Environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Set Up Database:**
   - Configure PostgreSQL and update `config.py` with credentials.
   - Apply migrations (if using Flask-Migrate):
     ```sh
     flask db upgrade
     ```
5. **Run Redis Server:**
   ```sh
   redis-server
   ```
6. **Start the Flask Server:**
   ```sh
   python3 app.py
   ```


## Deployment
- Use **Gunicorn** for production:
  ```sh
  gunicorn -w 4 -b 0.0.0.0:5000 app:app
  ```
- Deploy using **Docker**:
  ```sh
  docker-compose up --build
  ```

## Future Enhancements
- Expand multilingual support.
- Improve AI-based validation techniques.
- Optimize visualization capabilities.



