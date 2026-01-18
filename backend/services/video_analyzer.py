"""
Video Analyzer Service
Extracts metadata and transcripts from YouTube videos.
"""
import re
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build


class VideoAnalyzer:
    """Analyzes YouTube videos to extract metadata and transcripts."""

    def __init__(self, youtube_api_key: str):
        """
        Initialize the video analyzer.

        Args:
            youtube_api_key: YouTube Data API v3 key
        """
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        self.transcript_api = YouTubeTranscriptApi()

    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from various YouTube URL formats.

        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - https://www.youtube.com/live/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID

        Args:
            url: YouTube video URL

        Returns:
            Video ID string

        Raises:
            ValueError: If URL format is not recognized
        """
        patterns = [
            r'(?:youtube\.com\/watch\?v=)([^&\n?#]+)',
            r'(?:youtu\.be\/)([^&\n?#]+)',
            r'(?:youtube\.com\/embed\/)([^&\n?#]+)',
            r'(?:youtube\.com\/v\/)([^&\n?#]+)',
            r'(?:youtube\.com\/live\/)([^&\n?#]+)',
            r'(?:youtube\.com\/shorts\/)([^&\n?#]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        raise ValueError(f"Could not extract video ID from URL: {url}")

    def get_metadata(self, video_id: str) -> dict:
        """
        Fetch video metadata from YouTube Data API.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary containing title, description, tags, channel

        Raises:
            ValueError: If video is not found
        """
        request = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            raise ValueError(f"Video not found: {video_id}")

        snippet = response['items'][0]['snippet']

        return {
            'title': snippet.get('title', ''),
            'description': snippet.get('description', '')[:1000],  # Limit description length
            'tags': snippet.get('tags', [])[:20],  # Limit number of tags
            'channel': snippet.get('channelTitle', ''),
            'category_id': snippet.get('categoryId'),
            'published_at': snippet.get('publishedAt'),
        }

    def get_transcript(
        self,
        video_id: str,
        languages: list[str] = None,
        max_length: int = 5000
    ) -> Optional[str]:
        """
        Fetch video transcript/captions.

        Args:
            video_id: YouTube video ID
            languages: Preferred languages in order (default: ['en', 'en-US', 'en-GB'])
            max_length: Maximum transcript length to return

        Returns:
            Transcript text or None if unavailable
        """
        if languages is None:
            languages = ['en', 'en-US', 'en-GB']

        try:
            # Use the new fetch() API (youtube-transcript-api >= 1.0.0)
            transcript = self.transcript_api.fetch(video_id, languages=languages)

            # Combine text segments from the FetchedTranscript object
            full_text = ' '.join([
                snippet.text.replace('\n', ' ')
                for snippet in transcript
            ])

            # Limit length for LLM context
            return full_text[:max_length]

        except Exception as e:
            # Transcript not available - this is common and not an error
            print(f"Transcript not available for {video_id}: {e}")
            return None

    def analyze(self, url: str) -> dict:
        """
        Complete video analysis - metadata and transcript.

        Args:
            url: YouTube video URL

        Returns:
            Dictionary containing video_id, title, description, tags, channel, transcript
        """
        video_id = self.extract_video_id(url)
        metadata = self.get_metadata(video_id)
        transcript = self.get_transcript(video_id)

        return {
            'video_id': video_id,
            **metadata,
            'transcript': transcript,
        }
