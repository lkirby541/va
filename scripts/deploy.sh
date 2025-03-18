#!/bin/bash

# Initialize the system
docker-compose build
docker-compose up -d

# Wait for setup wizard
echo "Access https://localhost:8443 to complete setup"