import os
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq
from dotenv import load_dotenv

# =====================================================
# 🔑 Load Environment Variables
# =====================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =====================================================
# 🔑 Configure Groq API
# =====================================================
client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"


# =====================================================
# 1️⃣ Extract Video ID
# =====================================================
def extract_video_id(url):
    parsed = urlparse(url)

    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/live/"):
            return parsed.path.split("/live/")[1].split("?")[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1].split("?")[0]

    if parsed.hostname == "youtu.be":
        return parsed.path.split("?")[0][1:]

    if len(url) == 11 and "/" not in url:
        return url

    return None


# =====================================================
# 2️⃣ Fetch Transcript
# =====================================================
def fetch_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        for transcript in transcript_list:
            if not transcript.is_generated:
                fetched = transcript.fetch()
                return " ".join([entry.text for entry in fetched])

        for transcript in transcript_list:
            fetched = transcript.fetch()
            return " ".join([entry.text for entry in fetched])

        return None

    except Exception as e:
        print("❌ Transcript not available:", e)
        return None


# =====================================================
# 3️⃣ Split Transcript into Chunks
# =====================================================
def split_transcript(text, chunk_size=4000):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


# =====================================================
# 4️⃣ Call Groq Model
# =====================================================
def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a YouTube SEO strategist."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    return response.choices[0].message.content


# =====================================================
# 5️⃣ Summarize Each Chunk
# =====================================================
def summarize_chunks(chunks):

    summaries = []

    for i, chunk in enumerate(chunks):

        print(f"🧠 Summarizing chunk {i+1}/{len(chunks)}")

        prompt = f"""
Summarize the following podcast transcript section.

Focus on:
- key ideas
- important discussions
- main insights

TEXT:
{chunk}
"""

        summary = call_llm(prompt)
        summaries.append(summary)

    return "\n".join(summaries)


# =====================================================
# 6️⃣ Build Final SEO Prompt
# =====================================================
def build_final_prompt(summary):

    return f"""
You are an expert YouTube SEO strategist and Hindi content writer.

Analyze the following summarized transcript.

TRANSCRIPT SUMMARY
{summary}

---

TASK 1 — VIDEO TITLES (Hindi)

Write 10 highly clickable YouTube titles.

Rules:
- Natural Hindi
- 5–10 words
- Curiosity driven
- No colon

---

TASK 2 — SUMMARY (English)

Write a 4–6 line summary.

---

TASK 3 — DESCRIPTION (Hindi)

Write a compelling 3 line YouTube description.

---

TASK 4 — HASHTAGS

Write 6 SEO hashtags.

---

FORMAT:

TITLES:
1.
2.
3.
4.
5.
6.
7.
8.
9.
10.

SUMMARY:

DESCRIPTION:

HASHTAGS:
"""


# =====================================================
# 🚀 MAIN
# =====================================================
if __name__ == "__main__":

    print("\n🚀 AI YouTube Metadata Generator\n")

    url = input("Enter YouTube URL or ID: ").strip()

    video_id = extract_video_id(url)

    if not video_id:
        print("❌ Invalid URL")
        exit()

    print("📥 Fetching transcript...")
    transcript = fetch_transcript(video_id)

    if not transcript:
        print("❌ Transcript unavailable")
        exit()

    print("✂ Splitting transcript...")
    chunks = split_transcript(transcript)

    summary = summarize_chunks(chunks)

    print("🤖 Generating SEO metadata...")
    final_prompt = build_final_prompt(summary)

    result = call_llm(final_prompt)

    output_path = "output.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)

    print("✅ Output saved!")
    os.system(f'notepad.exe "{output_path}"')

    input("\nPress Enter to exit...")