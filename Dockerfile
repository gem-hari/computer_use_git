FROM 851725235990.dkr.ecr.ap-south-1.amazonaws.com/python-slim-11:3.11-slim
# FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .


# EXPOSE 5000
# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

EXPOSE 8501
CMD ["streamlit", "run", "computer_use_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]