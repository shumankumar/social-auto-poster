import os
import json
import requests

# Secrets बाट टोकनहरू तान्ने
FB_PAGE_ID = os.environ.get("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN")
IG_USER_ID = os.environ.get("IG_USER_ID")

def post_to_facebook(caption, media_url, media_type):
    """Facebook Page मा फोटो वा भिडियो पोस्ट गर्ने"""
    if not FB_PAGE_ID or not FB_ACCESS_TOKEN:
        print("Facebook credentials missing.")
        return None
        
    if media_type == "image":
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/photos"
        payload = {"url": media_url, "caption": caption, "access_token": FB_ACCESS_TOKEN}
    else:
        url = f"https://graph.facebook.com/v20.0/{FB_PAGE_ID}/videos"
        payload = {"file_url": media_url, "description": caption, "access_token": FB_ACCESS_TOKEN}
    
    res = requests.post(url, data=payload)
    data = res.json()
    if "id" in data:
        return data["id"]
    else:
        print(f"Facebook Error: {data}")
        return None

def post_to_instagram(caption, media_url, media_type):
    """Instagram Business Account मा पोस्ट गर्ने"""
    if not IG_USER_ID or not FB_ACCESS_TOKEN:
        print("Instagram credentials missing.")
        return None

    # १. मिडिया कन्टेनर बनाउने
    container_url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media"
    params = {"access_token": FB_ACCESS_TOKEN, "caption": caption}
    
    if media_type == "video":
        params["media_type"] = "REELS"
        params["video_url"] = media_url
    else:
        params["image_url"] = media_url

    res_init = requests.post(container_url, data=params).json()
    creation_id = res_init.get("id")

    if creation_id:
        # २. पब्लिश गर्ने
        publish_url = f"https://graph.facebook.com/v20.0/{IG_USER_ID}/media_publish"
        res_pub = requests.post(publish_url, data={"creation_id": creation_id, "access_token": FB_ACCESS_TOKEN}).json()
        return res_pub.get("id")
    else:
        print(f"Instagram Error: {res_init}")
        return None

def process_queue():
    if not os.path.exists("posts.json"):
        print("posts.json not found.")
        return

    with open("posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    updated = False
    for post in posts:
        # तपाईंले 'Approved' गरिदिनुभएका पोस्टहरू मात्र प्रक्रियामा जानेछन्
        if post.get("status") == "Approved":
            caption = post.get("caption", "")
            media_url = post.get("media_url", "")
            media_type = post.get("media_type", "image")
            platforms = post.get("platforms", [])

            print(f"Publishing Post ID {post.get('id')}...")

            if "facebook" in platforms:
                fb_id = post_to_facebook(caption, media_url, media_type)
                if fb_id:
                    print(f"Successfully posted to Facebook: {fb_id}")

            if "instagram" in platforms:
                ig_id = post_to_instagram(caption, media_url, media_type)
                if ig_id:
                    print(f"Successfully posted to Instagram: {ig_id}")

            # पोस्ट भइसकेपछि स्टेटस परिवर्तन गर्ने
            post["status"] = "Posted"
            updated = True
            break  # स्प्याम रोकथामका लागि एक पटकमा एउटा मात्र पोस्ट गर्ने

    if updated:
        with open("posts.json", "w", encoding="utf-8") as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print("posts.json updated.")

if __name__ == "__main__":
    process_queue()
