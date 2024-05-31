# Use an official Python runtime as a parent image
FROM python:3.10-slim

# using USER settings as recommended in this video https://www.youtube.com/watch?v=vP2JSAZLnRk
RUN useradd -m - u 1000 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory in the container
WORKDIR $HOME/climate-change-assistant

# Copy the current directory contents into the container
COPY . /climate-change-assistant

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Following instructions within HF docker file setup
COPY . .

# Run app.py when the container launches
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"]