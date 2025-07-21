import os
import json
import random
import httpx
import tiktoken
import logging
from openai import OpenAI
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeSearchTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3/search"
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search YouTube for ambience videos"""
        params = {
            "part": "snippet",
            "q": f"{query} ambience",
            "type": "video",
            "videoDuration": "long",  # >20 minutes
            "videoEmbeddable": "true",
            "maxResults": max_results,
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                videos = []
                for item in data.get("items", []):
                    videos.append({
                        "video_id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "channel": item["snippet"]["channelTitle"]
                    })
                
                return videos
            
            except httpx.HTTPError as e:
                raise Exception(f"YouTube API error: {str(e)}")

class AmbienceAgent:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.youtube_tool = YouTubeSearchTool(os.getenv("YOUTUBE_API_KEY"))
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Initialize tokenizer for the model
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.openai_model)
        except KeyError:
            # Fallback for newer models
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            logger.warning(f"Using fallback tokenizer for model: {self.openai_model}")
        
        # Define available moods and their associated keywords
        self.mood_keywords = {
            "tense": "dark thriller suspense",
            "romantic": "love romantic soft",
            "mystical": "magical fantasy ethereal",
            "peaceful": "calm relaxing nature",
            "epic": "cinematic heroic adventure",
            "melancholy": "sad emotional rain",
            "mysterious": "ambient dark mysterious",
            "cheerful": "upbeat happy bright",
            "dramatic": "intense emotional powerful",
            "serene": "peaceful meditation zen"
        }
    
    async def analyze_chapter_ambience(self, chapter_text: str) -> Dict:
        """Analyze chapter text and return mood + YouTube video ID"""
        
        # Extract random excerpts from chapter for analysis
        excerpts = self._extract_random_excerpts(chapter_text)
        
        # Classify mood using OpenAI
        mood = self._classify_mood(excerpts)
        
        # Search for appropriate YouTube video
        youtube_results = await self._search_youtube_for_mood(mood)
        
        # Select best video
        selected_video = self._select_best_video(youtube_results, mood)
        
        # Generate explanation for why this video was chosen
        explanation = self._generate_explanation(mood, selected_video)
        
        return {
            "mood": mood,
            "youtube_id": selected_video["video_id"],
            "video_title": selected_video["title"],
            "explanation": explanation
        }
    
    def _extract_random_excerpts(self, text: str, num_excerpts: int = 3, excerpt_length: int = 200) -> str:
        """Extract random excerpts from chapter text"""
        logger.info(f"🔍 EXTRACTING EXCERPTS - Chapter length: {len(text)} characters")
        
        sentences = text.split('. ')
        logger.info(f"📝 Total sentences in chapter: {len(sentences)}")
        
        if len(sentences) < num_excerpts:
            logger.warning(f"⚠️  Chapter too short ({len(sentences)} sentences), using full text")
            result = text[:excerpt_length * num_excerpts]
            logger.info(f"📋 Short chapter excerpt (first {len(result)} chars): {result[:100]}...")
            return result
        
        excerpts = []
        selected_indices = []
        for i in range(num_excerpts):
            start_idx = random.randint(0, max(0, len(sentences) - 5))
            selected_indices.append(start_idx)
            excerpt_sentences = sentences[start_idx:start_idx + 3]
            excerpt = '. '.join(excerpt_sentences)
            excerpt_trimmed = excerpt[:excerpt_length]
            excerpts.append(excerpt_trimmed)
            logger.info(f"📜 Excerpt {i+1} (sentences {start_idx}-{start_idx+2}): {excerpt_trimmed[:80]}...")
        
        final_excerpts = '\n\n---\n\n'.join(excerpts)
        logger.info(f"✅ Final excerpts combined length: {len(final_excerpts)} characters")
        logger.info(f"🎯 Selected sentence indices: {selected_indices}")
        
        return final_excerpts
    
    def _classify_mood(self, text_excerpts: str) -> str:
        """Use OpenAI to classify the mood of text excerpts"""
        logger.info("🎭 MOOD CLASSIFICATION STARTING")
        
        available_moods = list(self.mood_keywords.keys())
        mood_list = ", ".join(available_moods)
        
        prompt = f"""Analyze the following text excerpts and classify the overall mood/atmosphere in ONE word.

Choose from these moods: {mood_list}

Consider the emotional tone, setting, action level, and atmosphere described in the text.

Text excerpts:
{text_excerpts}

Respond with only the mood word, nothing else."""

        # Calculate token usage
        prompt_tokens = len(self.tokenizer.encode(prompt))
        logger.info(f"🔢 Estimated input tokens: {prompt_tokens}")
        logger.info(f"🤖 Using model: {self.openai_model}")
        logger.info(f"📤 PROMPT BEING SENT TO OPENAI:")
        logger.info("=" * 80)
        logger.info(prompt)
        logger.info("=" * 80)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            mood = response.choices[0].message.content.strip().lower()
            
            # Log the response
            logger.info(f"📥 RAW OPENAI RESPONSE: '{mood}'")
            logger.info(f"💰 Token usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            
            # Validate mood is in our list
            if mood in self.mood_keywords:
                logger.info(f"✅ MOOD CLASSIFICATION SUCCESS: '{mood}' (valid)")
                return mood
            else:
                logger.warning(f"⚠️  Invalid mood returned: '{mood}', attempting to find closest match")
                # Try to find closest match
                closest = self._find_closest_mood(mood)
                if closest:
                    logger.info(f"🔄 MOOD MAPPED: '{mood}' -> '{closest}'")
                    return closest
                else:
                    logger.error(f"❌ Could not map mood '{mood}' to any valid option")
                    logger.error(f"Available moods: {available_moods}")
                    raise Exception(f"Could not classify mood from text")
                
        except Exception as e:
            logger.error(f"❌ MOOD CLASSIFICATION ERROR: {str(e)}")
            raise Exception(f"Error classifying mood: {str(e)}")
    
    def _find_closest_mood(self, mood: str) -> str | None:
        """Find closest matching mood from available options"""
        mood = mood.lower()
        
        # Simple keyword matching
        mood_mappings = {
            "dark": "tense",
            "happy": "cheerful",
            "sad": "melancholy",
            "scary": "tense",
            "action": "epic",
            "love": "romantic",
            "magic": "mystical",
            "quiet": "peaceful",
            "calm": "serene"
        }
        
        for keyword, mapped_mood in mood_mappings.items():
            if keyword in mood:
                return mapped_mood
        
        return None
    
    async def _search_youtube_for_mood(self, mood: str) -> List[Dict]:
        """Search YouTube for videos matching the mood"""
        logger.info(f"🎥 YOUTUBE SEARCH STARTING for mood: '{mood}'")
        
        keywords = self.mood_keywords.get(mood)
        if not keywords:
            logger.error(f"❌ Unknown mood: '{mood}' not in mood_keywords")
            raise Exception(f"Unknown mood: {mood}")
            
        search_query = f"{keywords} ambient soundscape"
        logger.info(f"🔍 YouTube search query: '{search_query}'")
        
        try:
            videos = await self.youtube_tool.search(search_query)
            logger.info(f"📺 Found {len(videos)} YouTube videos")
            for i, video in enumerate(videos):
                logger.info(f"  Video {i+1}: {video['title']} (ID: {video['video_id']})")
            return videos
        except Exception as e:
            logger.error(f"❌ YouTube search error: {str(e)}")
            raise Exception(f"Error searching YouTube: {str(e)}")
    
    def _select_best_video(self, videos: List[Dict], mood: str) -> Dict:
        """Select the best video from search results"""
        logger.info(f"🎯 VIDEO SELECTION STARTING for mood: '{mood}'")
        
        if not videos:
            logger.error("❌ No videos found for this mood")
            raise Exception("No videos found for this mood")
        
        # Simple scoring based on title keywords
        keywords = self.mood_keywords.get(mood)
        if not keywords:
            logger.error(f"❌ Unknown mood: '{mood}' not in mood_keywords")
            raise Exception(f"Unknown mood: {mood}")
            
        mood_keywords = keywords.split()
        logger.info(f"🔑 Keywords for '{mood}': {mood_keywords}")
        
        best_video = videos[0]
        best_score = 0
        scoring_details = []
        
        for i, video in enumerate(videos):
            score = 0
            title_lower = video["title"].lower()
            score_breakdown = []
            
            # Score based on keyword matches
            for keyword in mood_keywords:
                if keyword in title_lower:
                    score += 1
                    score_breakdown.append(f"keyword '{keyword}' (+1)")
            
            # Prefer videos with "ambience" or "ambient" in title
            if "ambience" in title_lower or "ambient" in title_lower:
                score += 2
                score_breakdown.append("has 'ambient/ambience' (+2)")
            
            scoring_details.append({
                "video": video["title"],
                "score": score,
                "breakdown": score_breakdown
            })
            
            if score > best_score:
                best_score = score
                best_video = video
        
        # Log all scoring details
        logger.info("📊 VIDEO SCORING RESULTS:")
        for detail in scoring_details:
            logger.info(f"  {detail['score']}: {detail['video'][:60]}... - {', '.join(detail['breakdown']) if detail['breakdown'] else 'no matches'}")
        
        logger.info(f"🏆 SELECTED VIDEO: '{best_video['title']}' (score: {best_score})")
        return best_video
    
    def _generate_explanation(self, mood: str, selected_video: Dict) -> str:
        """Generate a one-sentence explanation for why this video was chosen"""
        try:
            prompt = f"""Explain in ONE sentence why the video "{selected_video['title']}" was chosen for a "{mood}" mood while reading.

Keep it concise and focus on how the video's atmosphere matches the chapter's emotional tone.

Example: "This video was selected because its dark atmospheric sounds perfectly complement the tense and suspenseful mood of this chapter."

Video title: {selected_video['title']}
Mood: {mood}
Video description: {selected_video.get('description', 'No description available')[:100]}"""

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            # Fallback explanation if AI generation fails
            return f"Selected for its {mood} atmosphere that matches the chapter's emotional tone."