# 🎵 Social Music Backend API

A backend system for a social music platform that allows users to register, authenticate, create posts, and interact through comments. The project focuses on building a secure, scalable REST API using modern backend development practices.

---

## 🚀 Features

* User registration and authentication system
* Secure login using JWT-based authentication
* Password hashing for secure credential storage
* Create, read, update, and delete (CRUD) operations for posts
* Comment system for user interaction on posts
* Role-based authorization and protected routes
* Relational database design for users, posts, and comments
* Dockerized environment for easy setup and deployment

---

## 🧱 Tech Stack

* **Backend:** Python, FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Authentication:** JWT (JSON Web Tokens)
* **Security:** Password hashing (bcrypt / passlib)
* **DevOps:** Docker, Docker Compose
* **Validation:** Pydantic

---

## 🏗️ Architecture Overview

The project follows a modular backend architecture:

* **API Layer:** FastAPI routes handling HTTP requests
* **Service Layer:** Business logic separation
* **Data Layer:** SQLAlchemy models and database interaction
* **Security Layer:** Authentication, JWT handling, password hashing

This separation ensures maintainability, scalability, and clean code organization.

---

## 🔐 Authentication Flow

1. User registers with email and password
2. Password is hashed before storing in database
3. User logs in and receives a JWT token
4. Token is used to access protected endpoints
5. Token expiration ensures session security

---

## 🐳 Running the Project with Docker

```bash
docker-compose up --build
```

The API will be available at:

```
http://localhost:8000
```

---

## 📡 API Endpoints (Example)

### Auth

* `POST /register` – Create a new user
* `POST /login` – Authenticate user and return JWT

### Posts

* `GET /posts` – Get all posts
* `POST /posts` – Create a post
* `DELETE /posts/{id}` – Delete a post

### Comments

* `POST /comments` – Add comment to post
* `GET /posts/{id}/comments` – Get comments for a post

---

## 🧪 Future Improvements

* Pagination for posts and comments
* User profiles
* Like system for posts
* Rate limiting
* Unit and integration tests
* CI/CD pipeline

---

## 📌 Project Goal

This project was built to strengthen backend engineering skills, focusing on:

* REST API design
* Authentication systems
* Database modeling
* Docker-based development environments
* Clean backend architecture principles

---

## 👤 Author

**Gabriel Rial Picco**

* GitHub: [your-link]
* LinkedIn: [your-link]

---