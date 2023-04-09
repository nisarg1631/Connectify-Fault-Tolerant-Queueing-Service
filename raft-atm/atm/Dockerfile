FROM python:3.8-slim-buster

# Copy requirements.txt first. Thus, only if requirements.txt changed will the RUN statement be executed.
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the rest of the directory
COPY . /app

CMD ["python3", "app.py"]