# Vastr-Fashion-Intelligence-Platform

> A full-stack fashion aggregation platform with a hybrid search engine, automated multi-brand data sync, and a production-style REST API layer.

Vastr pulls product data from multiple fashion brands into a single, searchable catalog. Instead of browsing seven different store websites, users get one unified search experience with real-time price and inventory tracking, wishlists, and advanced filtering — powered by a search engine that blends keyword relevance with semantic similarity.

---

## Why this exists

Most "aggregator" projects either do plain keyword search (fast, but misses relevant results with different wording) or pure embedding-based semantic search (flexible, but slow and sometimes returns loosely related results). Vastr combines both: a **BM25 keyword scorer** for precision on exact terms (brand names, sizes, colors) fused with **cosine similarity** over product embeddings for semantic relevance (finding "summer dress" matches even when the listing says "floral sundress"). The two scores are blended into a single ranked result set, giving more accurate results than either method alone.

On top of search, the platform also solves a harder, less glamorous problem: keeping data fresh. Prices, stock, and product listings change constantly across brand sites, so Vastr runs automated scraping and sync jobs to keep the catalog current rather than relying on a one-time data dump.

---

## How it works

```
Brand websites (7 sources)
        │
        ▼
Scraper / sync pipeline  →  raw product data (price, stock, images, metadata)
        │
        ▼
Normalizer  →  clean, structured product records (MongoDB)
        │
        ▼
Hybrid Search Engine
   ├── BM25 (keyword relevance)
   └── Cosine Similarity (semantic relevance)
        │
        ▼
Ranked, filtered results  →  React frontend (search, wishlist, filters)
```

- **Data sync:** Scheduled scraping jobs monitor 7 brand sources, tracking price changes and inventory updates automatically — no manual re-import needed.
- **Search:** Every query is scored two ways (keyword + semantic) and merged into a single ranked list.
- **API layer:** 19 RESTful endpoints handle auth, search, filtering, and wishlist functionality, built for real client consumption rather than a single demo page.

---

## Features

-  Hybrid search combining BM25 + cosine similarity
-  Automated data synchronization across 10+ brands (20,000+ products)
-  Real-time price change and inventory tracking
-  User authentication and wishlist support
-  Advanced filtering (price, brand, category, and more)
-  19 RESTful APIs powering the full frontend experience

---

## Tech stack

- **Backend:** FastAPI, Python
- **Database:** MongoDB
- **Search:** BM25 + cosine similarity (hybrid ranking)
- **Frontend:** React.js
- **Data pipeline:** Automated scraping & sync jobs

---

## Project structure

```
vastr/
├── backend/
│   ├── api/            # REST endpoints (auth, search, wishlist, filters)
│   ├── scraper/         # Brand data collection & sync jobs
│   ├── search/          # Hybrid search engine (BM25 + cosine similarity)
│   └── models/          # MongoDB schemas
├── frontend/
│   └── src/             # React application
└── README.md
```

---

## Getting started

```bash
# Clone the repo
git clone https://github.com/mahamusharaf/Vastr-Fashion-Intelligence-Platform.git
cd Vastr-Fashion-Intelligence-Platform

# Backend setup
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend setup
cd ../frontend
npm install
npm run dev
```

---

## Author

**Mahrukh Musharaf**
[GitHub](https://github.com/mahamusharaf) · [LinkedIn](https://www.linkedin.com/in/mahrukh-musharaf-4b1241304)
