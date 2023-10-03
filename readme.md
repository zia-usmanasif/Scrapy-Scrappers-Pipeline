# Scrapy Site Scraping with S3 Pipeline and Container Orchestration using Fargate

Welcome to the Scrapy Site Scraping with S3 Export project! This readme provides you with all the information you need to get started with web scraping using Scrapy and exporting your scraped data to an Amazon S3 bucket.

## Table of Contents

- [Project Overview](#project-overview)
- [Installation](#installation)

## Project Overview

This project uses Scrapy, a powerful web scraping framework, to extract data from websites. Additionally, it leverages the [Scrapy-S3Pipeline](https://github.com/orangain/scrapy-s3pipeline) package and [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) to export the scraped data directly to an Amazon S3 bucket. This combination provides a seamless and efficient way to collect, store, and analyze web data.

## Installation

This project is dockerized, making it easy to run within a containerized environment. You can use the provided Docker Compose file to set up and run the scraper with Selenium configuration.

To run the scraper using Docker Compose, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.

2. In the project directory, run the following command:

   ```bash
   docker-compose up
   ```

This will start the scraper in a Docker container with the Selenium configuration.
