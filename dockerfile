# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /climate-change-assistant

# Copy the current directory contents into the container at /app
COPY . /climate-change-assistant

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 80

# Run app.py when the container launches
CMD ["chainlit", "run", "app.py"]
