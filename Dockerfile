# Use the AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ENTIRE APPLICATION CODE into the container at /app
# This will copy your local 'app/' directory into '/app/app' inside the container
COPY . .

# Expose the port that Uvicorn will run on (This line is optional for Lambda but useful for local testing)
EXPOSE 8000

# Set the CMD to run the application (Note: Lambda automatically handles the invocation via the runtime interface)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]