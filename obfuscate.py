import json
import random
import string
import copy
import hashlib
from datetime import datetime, timedelta
import numpy as np
import re

# Set random seed for reproducibility
random.seed(42)

# Load the data
with open('data/urls.json', 'r', encoding='utf-8') as f:
    urls_data = json.load(f)
    
with open('data/comments.json', 'r', encoding='utf-8') as f:
    comments_data = json.load(f)

def hash_string(input_string, length=12):
    """Generate a consistent hash for a given string"""
    hash_object = hashlib.md5(input_string.encode())
    # Take first 'length' characters of the hexadecimal representation
    return hash_object.hexdigest()[:length]

def hash_to_number(input_string, min_val, max_val):
    """Generate a consistent number within range based on input string"""
    hash_val = int(hashlib.md5(input_string.encode()).hexdigest(), 16)
    return min_val + (hash_val % (max_val - min_val + 1))

def modify_number_consistently(number, seed_string):
    """Modify a number consistently based on a seed string"""
    hash_val = int(hashlib.md5(seed_string.encode()).hexdigest(), 16)
    random.seed(hash_val)
    modification = random.uniform(0.5, 1.5)
    random.seed()  # Reset random seed
    return int(int(number) * modification)

def generate_random_date_consistently(seed_string, start_year=2020):
    """Generate a consistent random date based on seed string"""
    start = datetime(start_year, 1, 1)
    end = datetime.now()
    days_between = (end - start).days
    hash_val = int(hashlib.md5(seed_string.encode()).hexdigest(), 16)
    random_days = hash_val % days_between
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d %H:%M:%S")

def obfuscate_url(url):
    """Consistently obfuscate TikTok URL while maintaining structure"""
    # Make pattern more flexible by making 'www.' optional
    pattern = r'https://(www\.)?tiktok\.com/@(.*?)/video/(\d+)'
    match = re.match(pattern, url)
    if not match:
        return url
    
    # Groups will now be: (www. or None, username, video_id)
    username, video_id = match.groups()[1:]  # Skip the first group (www.)
    
    # Generate consistent hashed versions
    hashed_username = hash_string(username, 8)
    hashed_video_id = hash_string(video_id, 19)  # TikTok video IDs are typically 19 digits
    
    # Always use www. in the output for consistency
    return f'https://www.tiktok.com/@{hashed_username}/video/{hashed_video_id}'

# Create mapping for original to obfuscated URLs
url_mapping = {url: obfuscate_url(url) for url in urls_data.keys()}
url_comments_mapping = {url: obfuscate_url(url) for url in comments_data.keys()}

# Randomly delete some videos and their associated comments
deletion_rate = 0.999
urls_to_delete = random.sample(list(urls_data.keys()), 
                             k=int(len(urls_data) * deletion_rate))
urls_to_delete_comments = random.sample(list(comments_data.keys()), 
                             k=int(len(comments_data) * deletion_rate))

# Create new dictionaries for obfuscated data
obfuscated_urls = {}
obfuscated_comments = {}

# Process URLs and comments with obfuscated keys
for original_url, data in urls_data.items():
    if original_url not in urls_to_delete:
        obfuscated_url = url_mapping[original_url]
        obfuscated_urls[obfuscated_url] = copy.deepcopy(data)

for original_url, comments_list in comments_data.items():
    if original_url not in urls_to_delete_comments:
        obfuscated_url = url_comments_mapping[original_url]
        obfuscated_comments[obfuscated_url] = copy.deepcopy(comments_list)

# Obfuscate comments
for url, comments_list in obfuscated_comments.items():
    for comment in comments_list:
        # Use original values as seeds for consistent hashing
        original_user_id = comment['user_id']
        comment['user_id'] = hash_string(original_user_id, 24)
        comment['user_name'] = hash_string(original_user_id + '_name', 12)
        comment['like_count'] = str(modify_number_consistently(
            comment['like_count'] if comment['like_count'].isdigit() else '0',
            original_user_id + '_likes'
        ))

# Obfuscate URLs data
for url, video_data in obfuscated_urls.items():
    # Obfuscate user information consistently
    for user in video_data['users']:
        original_user_id = user['user_id']
        user['user_id'] = hash_string(original_user_id, 24)
        user['user_name'] = hash_string(original_user_id + '_name', 12)
    
    if 'tagged' in video_data['text']:
        video_data['text']['tagged'] = [
            hash_string(tag + '_tagged', 12) for tag in video_data['text']['tagged']
        ]
    
    # Obfuscate music information
    original_music = video_data['music']['title']
    video_data['music']['title'] = hash_string(original_music, 15)
    video_data['music']['author_name'] = hash_string(original_music + '_author', 12)
    
    # Obfuscate video metadata
    original_video_id = video_data['video']['id']
    video_data['video']['id'] = hash_string(original_video_id, 32)
    video_data['video']['createTime'] = generate_random_date_consistently(original_video_id)
    video_data['video']['duration'] = hash_to_number(original_video_id + '_duration', 5, 60)
    video_data['video']['bitrate'] = hash_to_number(original_video_id + '_bitrate', 1000000, 5000000)
    
    # Randomize stats consistently
    stats_seed = original_video_id + '_stats'
    video_data['stats']['diggCount'] = modify_number_consistently(
        video_data['stats']['diggCount'], stats_seed + '_digg')
    video_data['stats']['shareCount'] = modify_number_consistently(
        video_data['stats']['shareCount'], stats_seed + '_share')
    video_data['stats']['commentCount'] = modify_number_consistently(
        video_data['stats']['commentCount'], stats_seed + '_comment')
    video_data['stats']['playCount'] = modify_number_consistently(
        video_data['stats']['playCount'], stats_seed + '_play')

# Save obfuscated data
with open(f'data_obs/obfuscated_urls_{deletion_rate}.json', 'w', encoding='utf-8') as f:
    json.dump(obfuscated_urls, f, ensure_ascii=False, indent=2)
    
with open(f'data_obs/obfuscated_comments_{deletion_rate}.json', 'w', encoding='utf-8') as f:
    json.dump(obfuscated_comments, f, ensure_ascii=False, indent=2)

print(f"Original number of videos: {len(urls_data)}")
print(f"Obfuscated number of videos: {len(obfuscated_urls)}")
print(f"Number of videos deleted: {len(urls_data) - len(obfuscated_urls)}")
print(f"Original number of video (in comments): {len(comments_data)}")
print(f"Obfuscated number of videos: {len(obfuscated_comments)}")
print(f"Number of videos deleted: {len(comments_data) - len(obfuscated_comments)}")