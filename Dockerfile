# Use an official lightweight Python image as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir keeps the image size smaller
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /app
# This includes app.py, quiz_logic.py, ui_pages.py, dataset.csv, etc.
COPY . .

# IMPORTANT: Run the model training script during the image build process.
# This pre-trains the models and creates the /models directory inside the image,
# so the app is ready to go when it starts.
RUN python train_model.py

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define the command to run your app using streamlit
# The --server.address=0.0.0.0 flag is crucial to make it accessible
# from outside the container (i.e., from your browser).
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
