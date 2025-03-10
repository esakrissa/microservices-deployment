FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
python -m app.subscriber &\n\
uvicorn app.main:app --host 0.0.0.0 --port 8080\n' > /app/start.sh && \
    chmod +x /app/start.sh

CMD ["/app/start.sh"]