import os
import openai
import requests
import logging
from typing import List
import backoff
from bs4 import BeautifulSoup
import praw
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

class TrendAnalyzer:
    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def get_tech_trends(self) -> List[str]:
        """Get trending tech topics from multiple sources"""
        trends = []
        
        # Reddit trends
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="VA/1.0"
            )
            subreddits = ["programming", "technology", "webdev"]
            for submission in reddit.subreddit("+".join(subreddits)).hot(limit=15):
                trends.extend(submission.title.split()[:5])
        except Exception as e:
            logging.error(f"Reddit trend error: {str(e)}")
        
        # Google Trends
        try:
            response = requests.get("https://trends.google.com/trends/api/dailytrends?geo=US")
            soup = BeautifulSoup(response.text, 'html.parser')
            trends += [t.text for t in soup.find_all('title')[:10]]
        except Exception as e:
            logging.error(f"Google Trends error: {str(e)}")
        
        return list(set(trends))[:10]  # Dedupe and return top 10

class ContentGenerator:
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
    
    @backoff.on_exception(backoff.expo, openai.error.APIError, max_tries=3)
    def generate_content_batch(self, num_items: int = 5) -> List[str]:
        """Generate multiple content pieces using current trends"""
        trends = self.trend_analyzer.get_tech_trends()
        prompt = f"""
        Generate {num_items} funny IT merchandise phrases (max 8 words each) 
        incorporating these trends: {', '.join(trends[:3])}.
        Mix these elements:
        - Tech jargon (e.g., API, Kubernetes)
        - Pop culture references
        - Programming humor
        - System admin struggles

        Examples:
        - "There's no place like 127.0.0.1"
        - "sudo make me a sandwich"
        - "I ❤️ CSS in 1996"
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative IT humor specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return [
            line.strip().strip('"') 
            for line in response.choices[0].message['content'].split('\n')
            if line.strip()
        ][:num_items]

    def generate_seo_title(self, content: str) -> str:
        """Create SEO-optimized listing title"""
        prompt = f"""
        Create an Etsy SEO title under 60 characters for: {content}
        Include relevant keywords and proper formatting.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=60
        )
        return response.choices[0].message['content'].strip('"')

    def generate_description(self, content: str) -> str:
        """Create product description with keywords"""
        prompt = f"""
        Write an engaging Etsy product description for: {content}
        Include:
        - 3 emojis
        - 2 hashtags
        - Technical humor
        - Call to action
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        return response.choices[0].message['content'].strip('"')