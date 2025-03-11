from fastapi import FastAPI
from marketplace_scraper import crawl_facebook_marketplace, clear_excel
import logging
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create an instance of the FastAPI class.
app = FastAPI()

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# Endpoint to crawl the Facebook Marketplace
@app.get("/crawl_facebook_marketplace")
def crawl_facebook_marketplace_endpoint(city: str, query: str, max_price: int):
    return crawl_facebook_marketplace(city, query, max_price)

@app.get("/clear")
def clear():
    return clear_excel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        'app:app',
        host='127.0.0.1',
        port=8000
    )
