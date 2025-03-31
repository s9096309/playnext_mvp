# PlayNext MVP

PlayNext MVP is a backend API built with FastAPI, designed to manage game-related data, user interactions, and provide game recommendations.

## Project Structure

playnext_mvp/
├── alembic/              # Database migration tool
├── app/
│   ├── database/
│   │   ├── init.py
│   │   ├── crud.py        # Database CRUD operations
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── schemas.py     # Pydantic schemas for data validation
│   │   └── session.py     # Database session management
│   ├── routers/
│   │   ├── init.py
│   │   ├── auth.py        # Authentication routes
│   │   ├── backlog_items.py # Backlog items routes
│   │   ├── games.py       # Game routes
│   │   ├── ratings.py     # Rating routes
│   │   ├── recommendations.py # Recommendation routes
│   │   └── users.py       # User routes
│   ├── utils/
│   │   ├── init.py
│   │   ├── main.py        # Main FastAPI application
│   │   └── recommendations_utils.py # Utility functions for recommendations
├── static/                # Static files (HTML, CSS)
│   ├── index.html
│   ├── rating.html
│   └── style.css
├── .env                   # Environment variables
├── .gitignore             # Git ignore file
├── alembic.ini            # Alembic configuration
└── encrypt_script.py      # Script for encrypting sensitive data

## Features

-   **User Authentication:** Secure user authentication using JWT.
-   **Game Management:** CRUD operations for games.
-   **User Ratings:** Ability to rate games.
-   **Backlog Management:** Manage user game backlogs.
-   **Game Recommendations:** Generate game recommendations using the Gemini API.
-   **Database Migrations:** Database schema management using Alembic.

## Getting Started

### Prerequisites

-   Python 3.7+
-   PostgreSQL

### PostgreSQL Setup

1.  **Install PostgreSQL:**

    -   **macOS:** You can use Homebrew: `brew install postgresql`
    -   **Linux (Debian/Ubuntu):** `sudo apt-get update && sudo apt-get install postgresql postgresql-contrib`
    -   **Windows:** Download the installer from the official PostgreSQL website: [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

2.  **Start the PostgreSQL server:**

    -   **macOS (Homebrew):** `brew services start postgresql`
    -   **Linux (systemd):** `sudo systemctl start postgresql`
    -   **Windows:** The installer should start the service automatically.

3.  **Create a database and user:**

    -   Open a terminal and run `psql postgres`.
    -   Create a new database: `CREATE DATABASE playnext;`
    -   Create a new user: `CREATE USER playnext_user WITH PASSWORD 'your_password';`
    -   Grant privileges to the user: `GRANT ALL PRIVILEGES ON DATABASE playnext TO playnext_user;`
    -   Exit psql: `\q`

### Installation

1.  **Clone the repository:**

    ```bash
    git clone [repository_url]
    cd playnext_mvp
    ```

2.  **Create a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On macOS and Linux
    venv\Scripts\activate    # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    -   Create a `.env` file in the root directory.
    -   Add the necessary environment variables (e.g., database connection string, JWT secret key, Gemini API key).

    Example `.env`:

    ```
    DATABASE_URL=postgresql://playnext_user:your_password@localhost/playnext
    SECRET_KEY=your_secret_key
    GEMINI_API_KEY=your_gemini_api_key
    ```

5.  **Run database migrations:**

    ```bash
    alembic upgrade head
    ```

6.  **Run the application:**

    ```bash
    uvicorn app.utils.main:app --reload
    ```

    The API will be accessible at `http://127.0.0.1:8000`.

## API Endpoints

-   **Authentication:**
    -   `/auth/token` (POST): Obtain JWT token.
-   **Users:**
    -   `/users/` (POST): Create a new user.
    -   `/users/{user_id}` (GET): Get user details.
    -   `/users/me/backlog` (GET): Get user's backlog.
-   **Games:**
    -   `/games/` (POST): Create a new game.
    -   `/games/{game_id}` (GET): Get game details.
-   **Ratings:**
    -   `/ratings/` (POST): Create a new rating.
    -   `/ratings/{rating_id}` (GET): Get rating details.
-   **Backlog Items:**
    -   `/backlog/` (POST): Create a new backlog item.
    -   `/backlog/{backlog_id}` (GET): Get backlog item details.
-   **Recommendations:**
    -   `/recommendations/user` (POST): Get game recommendations for a user.

## Technologies Used

-   FastAPI
-   SQLAlchemy
-   Pydantic
-   Alembic
-   JWT
-   Gemini API

## Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Submit a pull request.

## License

[MIT](LICENSE)