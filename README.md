# Redbook: Facebook Automation Modules

Redbook is a collection of functions designed to automate various tasks for a Facebook business page. These modules allow you to automatically post images or quotes stored in a database at scheduled intervals or using a time loop. Additionally, the modules can collect all posts from your Facebook page and store them locally in a database, bypassing the need for Facebook webhooks, which have strict production usage limitations until your application and business are approved. The modules also scan posts for comments, indexing them into a comments table that can be used for automatic replies.

## Function Overview and Use Cases

1. **Post images and quotes:** Schedule or set up a time loop to automatically post images and quotes from your database to your Facebook business page.

2. **Collect and store posts:** Retrieve all posts from your Facebook page and save them to a local database, allowing you to avoid using Facebook webhooks with strict production usage limitations.

3. **Index and reply to comments:** Scan the posts for comments, index them into a comments table, and iterate through them to generate automatic replies.

4. **Generate automatic replies with OpenAI ChatGPT:** Send user-inputted text to the OpenAI ChatGPT completion engine to generate a response. User questions are filtered by adding [Image] or [Question] before the text prompts. Image requests are processed using the DallE API.

## Environment Variables Setup

To set up the environment variables, you need to create or copy a `.env` file based on the provided `example.env`. Fill in the appropriate API keys and other settings to ensure the variables are loaded correctly.

## Functions and Use Cases

### Function 1: Post images and quotes

This function enables you to post images or quotes stored in a database to your Facebook business page at scheduled intervals or using a time loop.

**Use case:** Automate the process of posting images or quotes to your Facebook page, saving time and ensuring consistent content updates.

### Function 2: Collect and store posts

Retrieve all posts from your Facebook page and save them locally in a database, bypassing the need for Facebook webhooks.

**Use case:** Collect and store post data without relying on Facebook webhooks, which have production usage limitations.

### Function 3: Index and reply to comments

Scan the posts for comments, index them into a comments table, and iterate through them to generate automatic replies.

**Use case:** Efficiently manage user comments and provide timely responses to user inquiries or feedback.

### Function 4: Generate automatic replies with OpenAI ChatGPT

Send user-inputted text to the OpenAI ChatGPT completion engine to generate a response. Filter user questions by adding [Image] or [Question] before the text prompts. Process image requests using the DallE API.

**Use case:** Provide quick and relevant responses to user questions, improving user engagement and satisfaction.
