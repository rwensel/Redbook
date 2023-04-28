# Redbook
Facebook modules for posting automation

These are some functions I wrote to complete automated tasks for a Facebook business page. 
The modules provided will post images stored in a database, or quotes. You can set these on a time loop or schedule.
There are functions that will collect all posts on your Facebook page and store them locally to the database. 
This can be used to by pass using Facebook webhooks which are fully stricted from production use until you get your applican and business approved. 
The modules will also scan the post for comments and index them into a comments table which can then be iterated through for automatic replies.
One of the functions creates generates automatic replies by taking the users inputted text and sending it to the OpenAI ChatGTP completion engine which will generate a response. 
User questions are filtered by a user placing [Image] or [Question] before the text prompts. Images requests are processed using DallE API.

For environment variables you will need to copy or create a .env file like the example.env provided and place your api keys and other settings within the file for the variables to be properly loaded.
