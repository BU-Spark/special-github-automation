# Dockerfile for Vite React client

# Use the official Node.js image as the base image
FROM node:18

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install the dependencies
RUN npm install

# Copy the rest of the application code to the working directory
COPY . .

# Build the Vite project
RUN npm run build

# Install serve to serve the built files
RUN npm install -g serve

# Expose port 3000
EXPOSE 3000

# Command to serve the built files
CMD ["serve", "-s", "dist", "-l", "3000"]
