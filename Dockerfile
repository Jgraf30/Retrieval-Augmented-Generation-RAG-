FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV STORE_DIR=/app/store
ENV DATA_DIR=/app/data
EXPOSE 8501 8000

# Default to Streamlit UI; override command to run API if desired
CMD ["bash", "-lc", "streamlit run ui.py --server.port 8501 --server.address 0.0.0.0"]
