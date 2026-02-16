import os
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI


# ==============================
# 🔑 SET YOUR OPENAI API KEY
# ==============================
client = OpenAI(api_key="")


# ==============================
# 1️⃣ Extract Video ID
# ==============================
def extract_video_id(url):
    parsed = urlparse(url)

    # Standard YouTube URL
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]

    # Shortened URL
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]

    return None


# ==============================
# 2️⃣ Fetch Transcript
# ==============================
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except Exception as e:
        print("❌ Transcript not available:", e)
        return None


# ==============================
# 3️⃣ Create Prompt
# ==============================
def build_prompt(transcript):

    # Limit transcript size (important)
    transcript = transcript[:15000]

    return f"""
You are a professional YouTube SEO expert.

Analyze the transcript below and generate:

1. A highly clickable SEO-optimized title (max 60 characters)
2. A compelling description (200–300 words)
3. 10 strong relevant hashtags
4. A short 3–4 line summary

Make the title engaging and curiosity-driven.

Transcript:
{transcript}

Return output EXACTLY in this format:

TITLE:
...

DESCRIPTION:
...

HASHTAGS:
...

SUMMARY:
...
"""


# ==============================
# 4️⃣ Call LLM
# ==============================
def generate_content(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in YouTube growth and SEO."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        print("❌ Error generating content:", e)
        return None


# ==============================
# 5️⃣ Save Output (Optional)
# ==============================
def save_to_file(content, video_id):
    filename = f"metadata_{video_id}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ Saved to file: {filename}")


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":

    print("\n🚀 Video Metadata Generator\n")

    url = input("Enter YouTube Video URL: ").strip()

    video_id = extract_video_id(url)

    if not video_id:
        print("❌ Invalid YouTube URL")
        exit()

    print("\n📥 Fetching transcript...")
    transcript = fetch_transcript(video_id)

    if not transcript:
        print("❌ Could not retrieve transcript.")
        exit()

    print("🤖 Generating metadata...\n")

    prompt = build_prompt(transcript)
    result = generate_content(prompt)

    if result:
        print("\n" + "=" * 60)
        print("🎯 GENERATED CONTENT")
        print("=" * 60)
        print(result)
        print("=" * 60)

        # Save to file
        save_to_file(result, video_id)

    else:
        print("❌ Failed to generate metadata.")
