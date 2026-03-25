FROM python:3.11-slim

# set working directory inside container
WORKDIR /app

# copy requirements first (so Docker caches this layer)
COPY requirements.txt .

# install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# install Chrome browser (needed for Selenium)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# copy all scraper files into container
COPY . .

# default command runs the scraper
CMD ["python", "scraper_v2.py"]