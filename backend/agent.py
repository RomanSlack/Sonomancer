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
        
        # No more mood restrictions - agent has full creative freedom
    
    async def analyze_chapter_ambience(self, chapter_text: str) -> Dict:
        """Analyze chapter text and return ambient soundscape recommendation"""
        
        # Extract random excerpts from chapter for analysis
        excerpts = self._extract_random_excerpts(chapter_text)
        
        # Get creative ambient recommendation from OpenAI
        ambient_analysis = await self._analyze_for_ambience(excerpts)
        
        # Search YouTube for the recommended ambience
        youtube_results = await self._search_youtube_creative(ambient_analysis["search_terms"])
        
        # If no results, try a fallback search
        if not youtube_results:
            logger.warning("⚠️  No results from creative search, trying fallback")
            fallback_terms = "calm ambient background sounds for reading"
            youtube_results = await self._search_youtube_creative(fallback_terms)
        
        # Select best video with preference for calm, non-music content
        selected_video = self._select_best_ambient_video(youtube_results, ambient_analysis)
        
        # Generate explanation for why this video was chosen
        explanation = self._generate_explanation(ambient_analysis, selected_video)
        
        return {
            "mood": ambient_analysis["atmosphere"],
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
    
    async def _analyze_for_ambience(self, text_excerpts: str) -> Dict:
        """Use OpenAI to creatively analyze text and suggest ambient soundscape"""
        logger.info("🎨 CREATIVE AMBIENCE ANALYSIS STARTING")
        
        prompt = f"""You are an expert at creating immersive reading experiences through ambient soundscapes. 

Analyze the following text excerpts and suggest the perfect ambient background sounds that would enhance the reading experience. Be creative and specific about the type of ambience that would complement this text.

Prefer CALMER, more SUBTLE ambient sounds over loud music. Think environmental sounds, nature, gentle atmospheres, soft textures - not songs or intense music.

Text excerpts:
{text_excerpts}

Respond with ONLY a valid JSON object (no markdown, no code blocks, no extra text):

{{
    "atmosphere": "brief description of the overall feeling/atmosphere",
    "search_terms": "specific search terms for finding the perfect ambient sounds on YouTube (be creative and specific)",
    "reasoning": "why these ambient sounds would enhance the reading experience"
}}

Examples of good search terms:
- "gentle rain forest ambience"
- "cozy fireplace crackling sounds"
- "soft ocean waves distant"
- "library quiet ambient sounds"
- "medieval tavern background ambience"
- "space station ambient hum"
- "coffee shop background noise"

IMPORTANT: Return ONLY the JSON object, no markdown code blocks, no extra formatting."""

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
                max_tokens=150,
                temperature=0.7  # Higher temperature for more creativity
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Log the response
            logger.info(f"📥 RAW OPENAI RESPONSE: {response_text}")
            logger.info(f"💰 Token usage - Input: {response.usage.prompt_tokens}, Output: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code blocks if present
                json_text = response_text
                if "```json" in json_text:
                    # Extract content between ```json and ```
                    start = json_text.find("```json") + 7
                    end = json_text.find("```", start)
                    if end != -1:
                        json_text = json_text[start:end].strip()
                elif "```" in json_text:
                    # Handle generic code blocks
                    start = json_text.find("```") + 3
                    end = json_text.find("```", start)
                    if end != -1:
                        json_text = json_text[start:end].strip()
                
                analysis = json.loads(json_text)
                logger.info(f"✅ AMBIENCE ANALYSIS SUCCESS:")
                logger.info(f"  🌅 Atmosphere: {analysis['atmosphere']}")
                logger.info(f"  🔍 Search terms: {analysis['search_terms']}")
                logger.info(f"  💭 Reasoning: {analysis['reasoning']}")
                return analysis
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  JSON parsing failed: {str(e)}")
                logger.warning(f"Raw response: {response_text}")
                # Fallback parsing
                return self._parse_fallback_response(response_text)
                
        except Exception as e:
            logger.error(f"❌ AMBIENCE ANALYSIS ERROR: {str(e)}")
            raise Exception(f"Error analyzing ambience: {str(e)}")
    
    def _parse_fallback_response(self, response_text: str) -> Dict:
        """Parse non-JSON response as fallback"""
        logger.info("🔄 ATTEMPTING FALLBACK PARSING")
        
        # Try to extract meaningful information from the response
        lines = response_text.strip().split('\n')
        atmosphere = "ambient reading environment"
        search_terms = "calm ambient background sounds"
        reasoning = "AI generated ambient recommendation"
        
        # Look for key information in the response
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to find atmosphere descriptions
            if any(word in line.lower() for word in ["atmosphere", "feeling", "mood", "tone"]):
                # Extract description after colon or quotes
                if ":" in line:
                    potential_atmosphere = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if len(potential_atmosphere) > 3 and len(potential_atmosphere) < 100:
                        atmosphere = potential_atmosphere
                        
            # Try to find search terms
            if any(word in line.lower() for word in ["search", "terms", "sounds", "ambient"]):
                if ":" in line:
                    potential_search = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if len(potential_search) > 5 and len(potential_search) < 100:
                        search_terms = potential_search
                        
            # Try to find reasoning
            if any(word in line.lower() for word in ["reasoning", "because", "why", "enhance"]):
                if ":" in line:
                    potential_reasoning = line.split(":", 1)[1].strip().strip('"').strip("'")
                    if len(potential_reasoning) > 10 and len(potential_reasoning) < 200:
                        reasoning = potential_reasoning
        
        # If we couldn't parse anything useful, create something from the first part of the response
        if atmosphere == "ambient reading environment" and len(response_text) > 20:
            # Use first meaningful part as atmosphere description
            first_part = response_text[:100].strip()
            if first_part:
                atmosphere = first_part
                search_terms = f"{first_part[:30]} ambient background sounds"
        
        fallback_result = {
            "atmosphere": atmosphere,
            "search_terms": search_terms,
            "reasoning": reasoning
        }
        
        logger.info(f"🔄 FALLBACK PARSING RESULT:")
        logger.info(f"  🌅 Atmosphere: {fallback_result['atmosphere']}")
        logger.info(f"  🔍 Search terms: {fallback_result['search_terms']}")
        logger.info(f"  💭 Reasoning: {fallback_result['reasoning']}")
        
        return fallback_result
    
    async def _search_youtube_creative(self, search_terms: str) -> List[Dict]:
        """Search YouTube using creative search terms"""
        logger.info(f"🎥 CREATIVE YOUTUBE SEARCH STARTING")
        logger.info(f"🔍 Search terms: '{search_terms}'")
        
        try:
            videos = await self.youtube_tool.search(search_terms)
            logger.info(f"📺 Found {len(videos)} YouTube videos")
            for i, video in enumerate(videos):
                logger.info(f"  Video {i+1}: {video['title']} (ID: {video['video_id']})")
            return videos
        except Exception as e:
            logger.error(f"❌ YouTube search error: {str(e)}")
            raise Exception(f"Error searching YouTube: {str(e)}")
    
    def _select_best_ambient_video(self, videos: List[Dict], ambient_analysis: Dict) -> Dict:
        """Select the best ambient video with preference for calm, non-music content"""
        logger.info(f"🎯 AMBIENT VIDEO SELECTION STARTING")
        
        if not videos:
            logger.error("❌ No videos found")
            raise Exception("No videos found for this search")
        
        best_video = videos[0]
        best_score = 0
        scoring_details = []
        
        # Preferred ambient keywords (higher scores)
        ambient_keywords = [
            "ambience", "ambient", "soundscape", "atmosphere", "background",
            "nature", "rain", "forest", "ocean", "waves", "wind", "fire",
            "crackling", "peaceful", "calm", "quiet", "gentle", "soft",
            "relaxing", "meditation", "study", "reading", "library",
            "coffee", "cafe", "fireplace", "thunder", "birds", "water"
        ]
        
        # Music keywords (lower scores - we want to avoid these)
        music_keywords = [
            "music", "song", "melody", "beat", "rhythm", "bass", "drums",
            "guitar", "piano", "vocal", "lyrics", "album", "track",
            "playlist", "remix", "mix", "dj", "electronic", "synthwave"
        ]
        
        for i, video in enumerate(videos):
            score = 0
            title_lower = video["title"].lower()
            description_lower = video.get("description", "").lower()
            combined_text = f"{title_lower} {description_lower}"
            score_breakdown = []
            
            # High score for ambient keywords
            for keyword in ambient_keywords:
                if keyword in combined_text:
                    score += 3
                    score_breakdown.append(f"ambient word '{keyword}' (+3)")
            
            # Penalty for music keywords
            for keyword in music_keywords:
                if keyword in combined_text:
                    score -= 2
                    score_breakdown.append(f"music word '{keyword}' (-2)")
            
            # Extra points for long videos (usually better ambient content)
            if "hour" in combined_text or "hours" in combined_text:
                score += 2
                score_breakdown.append("long duration (+2)")
            
            # Extra points for specific calm descriptors
            calm_descriptors = ["gentle", "soft", "peaceful", "calm", "quiet", "subtle"]
            for descriptor in calm_descriptors:
                if descriptor in combined_text:
                    score += 2
                    score_breakdown.append(f"calm descriptor '{descriptor}' (+2)")
            
            # Avoid videos with these negative indicators
            avoid_keywords = ["loud", "intense", "epic", "powerful", "heavy", "metal"]
            for keyword in avoid_keywords:
                if keyword in combined_text:
                    score -= 3
                    score_breakdown.append(f"avoid word '{keyword}' (-3)")
            
            scoring_details.append({
                "video": video["title"],
                "score": score,
                "breakdown": score_breakdown
            })
            
            if score > best_score:
                best_score = score
                best_video = video
        
        # Log all scoring details
        logger.info("📊 AMBIENT VIDEO SCORING RESULTS:")
        for detail in scoring_details:
            breakdown_text = ', '.join(detail['breakdown']) if detail['breakdown'] else 'no specific matches'
            logger.info(f"  {detail['score']:3d}: {detail['video'][:50]}... - {breakdown_text}")
        
        logger.info(f"🏆 SELECTED AMBIENT VIDEO: '{best_video['title']}' (score: {best_score})")
        return best_video
    
    def _generate_explanation(self, ambient_analysis: Dict, selected_video: Dict) -> str:
        """Generate a one-sentence explanation for why this video was chosen"""
        try:
            atmosphere = ambient_analysis.get("atmosphere", "ambient reading environment")
            reasoning = ambient_analysis.get("reasoning", "enhances the reading experience")
            
            prompt = f"""Explain in ONE sentence why the ambient video "{selected_video['title']}" was chosen to enhance this reading experience.

Focus on how the ambient sounds complement the text's atmosphere and enhance immersion.

Chapter atmosphere: {atmosphere}
AI reasoning: {reasoning}
Video title: {selected_video['title']}
Video description: {selected_video.get('description', 'Ambient soundscape')[:100]}

Keep it natural and conversational."""

            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60,
                temperature=0.4
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info(f"💬 Generated explanation: {explanation}")
            return explanation
            
        except Exception as e:
            # Fallback explanation if AI generation fails
            fallback = f"Selected for its {atmosphere} ambience that enhances the reading atmosphere."
            logger.warning(f"⚠️  Using fallback explanation: {fallback}")
            return fallback