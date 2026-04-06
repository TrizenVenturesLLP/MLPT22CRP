FROM python:3.11-slim

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Install dependencies (do this before copying heavy model files if applicable to cache layers)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the gunicorn server on port 7860
# Port 7860 is REQUIRED by Hugging Face Spaces
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:7860", "--timeout", "600"]
