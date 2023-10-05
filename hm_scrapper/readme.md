# Scrapy Site Scraping with S3 Pipeline and Container Orchestration using Fargate

Welcome to the Scrapy Site Scraping with S3 Export project! This readme provides you with all the information you need to get started with web scraping using Scrapy and exporting your scraped data to an Amazon S3 bucket.

## Table of Contents

- [Project Overview](#project-overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Dockerization](#dockerization)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

This project uses Scrapy, a powerful web scraping framework, to extract data from websites. Additionally, it leverages the [Scrapy-S3Pipeline](https://github.com/orangain/scrapy-s3pipeline) package and [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) to export the scraped data directly to an Amazon S3 bucket. This combination provides a seamless and efficient way to collect, store, and analyze web data.

## Installation

Before you start, make sure you have Python and pip installed on your system. To install the required packages, please unzip the archive and after navigating into it, you can use pip:

```bash
pip install -r requirements.txt
```

## Configuration

To use this project effectively, you need to configure both Scrapy and the Scrapy-S3Pipeline. Here are the steps to do that:

1. **Scrapy Configuration:**

   - Unzip the scraper.
   - Customize your spiders to scrape the desired website(s) and save the data in a JSON format using the `-o` option (e.g., `scrapy crawl crawler-name -o output-file.json`).

2. **Replace AWS CREDENTIALS in .env file:**

## Usage

Once you've configured your project, you can start scraping websites and exporting data to your S3 bucket.

1. **Run a Spider:**

   - Use the following command to run a spider and export the scraped data to your S3 bucket:
     ```bash
     scrapy crawl crawler-name -o output-file.json
     ```
   - Replace `crawler-name` with the name of your spider and adjust the output file name as needed.

2. **View Exported Data:**
   - After running the spider, your scraped data will be automatically exported to the specified S3 bucket.

## Dockerization

This project is dockerized, making it easy to run within a containerized environment. You can use the provided Docker Compose file to set up and run the scraper with Selenium configuration.

To run the scraper using Docker Compose, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.

2. In the project directory, run the following command:

   ```bash
   docker-compose up
   ```

This will start the scraper in a Docker container with the Selenium configuration.

## Contributing

Contributions to this project are welcome. If you find any issues or have suggestions for improvements, please open an issue or submit a pull request on the [GitHub repository](https://github.com/your-repository-link).

## License

This project is licensed under the [MIT License](LICENSE), which means you are free to use, modify, and distribute the code for your own purposes.
