# Wander — Luxury Travel Guide Platform

![Wander Platform Demo](https://images.unsplash.com/photo-1506929562872-bb421503ef21?w=1920&q=80)

Wander is a premium, full-stack travel platform prototype designed to act as an immersive "digital guidebook." It seamlessly connects a Python-powered REST API backend with a completely custom, vanila JavaScript frontend to deliver curated travel data instantaneously.

## ✨ Features

* **Dynamic Data Rendering:** Destinations, experiences, and traveler reviews are loaded instantly from CSV datasets via the Python backend API.
* **Premium Editorial UI:** Designed entirely from scratch (No Bootstrap/Tailwind) following high-end luxury branding guidelines. Features frosted glass navbars, immersive parallax headers, and cinematic transitions.
* **Advanced UX & Interactivity:**
  * **Dark Mode:** A seamless toggle switches the entire application to an elegant deep-charcoal theme using CSS properties.
  * **Interactive Modals:** Clicking a destination card launches a full-screen, data-rich modal loaded with traveler reviews and specific destination stats.
  * **Live Filters & Sorting:** Sort by price, rating, or category (e.g. Beach, Culture) without a page reload.
  * **Custom Cursor:** Features a cinematic trailing-dot cursor that intelligently expands when hovering over interactive elements.
  * **Loading Skeletons:** Premium shimmering placeholders display gracefully while backend data is fetched.

## 🛠 Tech Stack

* **Frontend:** Pure HTML5, CSS3, and Vanilla JavaScript (No React/Vue, ensuring blazingly fast load times).
* **Backend:** Python + Flask (RESTful API architecture).
* **Data Layer:** Pandas (`pandas`), running off localized CSV files (simulating a Kaggle-sourced dataset).

## 🗂 Project Structure

```
├── index.html            # Main frontend application (UI & Logic)
├── app.py                # Python Flask backend server and API routes
├── requirements.txt      # Python dependencies for the backend
├── data/
│   ├── destinations.csv  # Tourism location dataset (Continent, Category, Cost)
│   ├── experiences.csv   # Categories & activity typologies
│   └── reviews.csv       # Traveler testimonials mapped to destinations
└── README.md             # Project documentation
```

## 🚀 How to Run Locally

1. **Clone or download** this repository to your local machine.
2. **Navigate into the project directory:**
   ```bash
   cd path/to/punam
   ```
3. **Install the Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start the Flask Backend Server:**
   ```bash
   python3 app.py
   ```
5. **View the Application:**
   Open your browser and navigate to `http://127.0.0.1:5050`. The backend automatically serves the frontend interface!

## ⚙️ API Endpoints

The Flask server provides the following RESTful routes for the frontend:
* `GET /api/destinations` — Fetches all destinations (supports `?category=`, `?sort=`, `?search=`).
* `GET /api/destinations/<id>` — Fetches a single destination along with its specific traveler reviews.
* `GET /api/experiences` — Fetches experience chips and counts.
* `GET /api/reviews` — Fetches the top recent reviews for the editorial section.
* `GET /api/stats` — Provides aggregate analytics about the datasets.
* `POST /api/newsletter` — Demo endpoint for capturing newsletter signups.

## 🎨 Modifying the Data
Because the frontend is entirely decoupled and dynamic, updating the platform does not require writing code! Simply open the `.csv` files inside the `/data` directory, modify the text, edit prices, or swap out `image_url` links, and the live website will dynamically reflect your changes upon the next refresh.
