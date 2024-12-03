# Calorie and Diet Plan Assistant

## Overview
This project includes a backend and frontend for a calorie and diet plan assistant. The backend is built using **FastAPI**, **Poetry**, **Langgraph**, and **LangChain**, while the frontend is built with **Next.js**, **TypeScript**, and **Tailwind CSS**.

- The **backend** calculates daily caloric needs based on the user's data and provides personalized diet plans.
- The **frontend** is a responsive web app that interacts with the backend API, providing users with a seamless experience to input their information and view their recommended calorie intake and diet plans.

## Table of Contents

1. [Backend (FastAPI with Poetry)](#backend-fastapi-with-poetry)
   - [Requirements](#requirements)
   - [Setup](#setup)
   - [API Documentation](#api-documentation)
   - [Running the Backend](#running-the-backend)
2. [Frontend (Next.js with TypeScript and Tailwind CSS)](#frontend-nextjs-with-typescript-and-tailwind-css)
   - [Requirements](#requirements-1)
   - [Running the Frontend](#running-the-frontend)
3. [Project Structure](#project-structure)
4. [Environment Variables](#environment-variables)

---

## Backend (FastAPI with Poetry)

### Requirements

- Python 3.x
- **Poetry** (for dependency management)
- FastAPI
- Uvicorn
- LangChain
- Langgraph
- Google Generative AI
- Tavily API
- FAISS
- dotenv
- pydantic
- Faiss-cpu
- beautifulsoup4





## Setup

1. **Clone the repository:**
git clone https://github.com/ehtasham11/nutritional-AI.git
cd nutritional-AI

2. **Create a .env file in the backend directory and add the following environment variables:**
- GOOGLE_API_KEY=your_google_api_key
- TAVILY_API_KEY=your_tavily_api_key

3. The backend uses the Google Generative AI API, Tavily API for search, and FAISS for vector-based searches.


## Running the Backend
poetry run python -m uvicorn main:app --port 8001 --reload

## Frontend (Next.js with TypeScript and Tailwind CSS)
**Requirements**
Node.js (v14 or higher)
npm
Tailwind CSS
TypeScript

## Environment Variables

- GOOGLE_API_KEY: API key for Google Generative AI
- TAVILY_API_KEY: API key for Tavily search
- API_URL: Base URL for the backend API (default: http://localhost:8001)
- Make sure to configure the .env file for the backend and frontend accordingly.

## Running the Frontend
**To run the frontend:**
npm run dev

## License

**This project is licensed under the MIT License - see the LICENSE file for details.**


### Steps to Convert This into `.md`:

1. Create a new file named `README.md` in the root directory of your project.
2. Copy and paste the markdown content above into this file.
3. Save the file.

Now, your `README.md` file should be ready! Let me know if you need further adjustments.
