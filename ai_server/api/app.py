#!/usr/bin/env python
from __future__ import unicode_literals
from nltk.tag import pos_tag
from nltk.tokenize import sent_tokenize
import numpy as np
from collections import defaultdict
from moviepy.editor import VideoFileClip, concatenate_videoclips
import pysrt
import chardet
import yt_dlp
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict
import tempfile
from datetime import datetime
import sys
import subprocess
import argparse

import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')


#!/usr/bin/env python

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('video_summarizer.log')
    ]
)
logger = logging.getLogger(__name__)


def time_regions(regions: List[Tuple[float, float]]) -> float:
    """Calculate total time duration for all regions."""
    return sum(end - start for start, end in regions)


def srt_segment_to_range(segment: pysrt.SubRipItem) -> Tuple[float, float]:
    """Convert subtitle segment to time range in seconds."""
    start = segment.start.hours * 3600 + segment.start.minutes * \
        60 + segment.start.seconds + segment.start.milliseconds / 1000
    end = segment.end.hours * 3600 + segment.end.minutes * \
        60 + segment.end.seconds + segment.end.milliseconds / 1000
    return start, end


class SentenceInfo:
    def __init__(self, text: str, start: float, end: float, duration: float, score: float = 0.0):
        self.text = text
        self.start = start
        self.end = end
        self.duration = duration
        self.score = score

    def __lt__(self, other):
        return self.score < other.score


def summarize(srt_file: pysrt.SubRipFile, max_summary_size: int) -> List[Tuple[float, float]]:
    """
    Create summary by extracting important segments based on:
    - Sentence importance (presence of nouns, verbs)
    - Segment duration
    - Content density
    """
    # Convert subtitles to list of sentences with timing
    sentences: List[SentenceInfo] = []
    for segment in srt_file:
        # Split segment text into sentences
        segment_sentences = sent_tokenize(segment.text)
        if not segment_sentences:
            continue

        timing = srt_segment_to_range(segment)
        duration = timing[1] - timing[0]

        # Handle single sentence case
        if len(segment_sentences) == 1:
            sentences.append(SentenceInfo(
                text=segment_sentences[0],
                start=timing[0],
                end=timing[1],
                duration=duration
            ))
        else:
            # Distribute time proportionally for multiple sentences
            time_per_char = duration / len(segment.text)
            current_time = timing[0]

            for sentence in segment_sentences:
                sentence_duration = len(sentence) * time_per_char
                sentences.append(SentenceInfo(
                    text=sentence,
                    start=current_time,
                    end=current_time + sentence_duration,
                    duration=sentence_duration
                ))
                current_time += sentence_duration

    # Score sentences based on various factors
    scored_sentences = []
    for sentence in sentences:
        # Analyze POS tags
        tokens = pos_tag(nltk.word_tokenize(sentence.text))
        num_nouns = sum(1 for _, pos in tokens if pos.startswith('NN'))
        num_verbs = sum(1 for _, pos in tokens if pos.startswith('VB'))

        # Calculate scores
        content_score = (num_nouns + num_verbs) / len(tokens) if tokens else 0
        # Favor medium-length sentences
        length_score = min(1.0, len(sentence.text) / 100)
        # Favor segments 2-5 seconds
        duration_score = min(1.0, sentence.duration / 5)

        total_score = content_score * 0.4 + length_score * 0.3 + duration_score * 0.3
        sentence.score = total_score
        scored_sentences.append(sentence)

    # Sort by score and select top segments
    scored_sentences.sort(reverse=True)
    selected_sentences = scored_sentences[:max_summary_size]

    # Sort selected sentences by time
    selected_sentences.sort(key=lambda x: x.start)

    # Merge overlapping or very close segments
    merged_regions = []
    if not selected_sentences:
        return merged_regions

    current_start = selected_sentences[0].start
    current_end = selected_sentences[0].end

    for sentence in selected_sentences[1:]:
        if sentence.start - current_end <= 0.5:  # Merge if gap is less than 0.5s
            current_end = sentence.end
        else:
            merged_regions.append((current_start, current_end))
            current_start = sentence.start
            current_end = sentence.end

    merged_regions.append((current_start, current_end))
    return merged_regions


class VideoSummarizer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp())
        self.setup_nltk()

    def setup_nltk(self):
        """Setup NLTK with required packages."""
        try:
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context

            nltk.download('punkt', quiet=True)
            nltk.download('averaged_perceptron_tagger', quiet=True)
        except Exception as e:
            logger.error(f"Failed to setup NLTK: {str(e)}")
            raise

    def check_dependencies(self) -> bool:
        """Check if required external dependencies are installed."""
        dependencies = ['ffmpeg']

        for dep in dependencies:
            try:
                subprocess.run([dep, '-version'], capture_output=True)
            except FileNotFoundError:
                logger.error(f"{dep} not found. Please install it first.")
                return False
        return True

    def download_video(self, url: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Download video and subtitles."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = self.temp_dir / f"video_{timestamp}"

        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': str(base_filename) + '.%(ext)s',
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'postprocessors': [{
                'key': 'FFmpegSubtitlesConvertor',
                'format': 'srt',
            }],
            'quiet': True,
            'no_warnings': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Downloading video...")
                print(type(url))
                info = ydl.extract_info(url, download=True)
                video_path = base_filename.with_suffix(f".{info['ext']}")
                subtitle_path = base_filename.with_suffix(".en.srt")

                if not video_path.exists():
                    logger.error("Video download failed")
                    return None, None

                if not subtitle_path.exists():
                    logger.warning(
                        "No subtitles found, attempting auto-generation...")
                    # Implement fallback subtitle generation here if needed

                return video_path, subtitle_path

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None, None

    def process_subtitles(self, subtitle_path: Path, duration: int = 60) -> List[Tuple[float, float]]:
        """Process subtitles and find summary regions."""
        try:
            with open(subtitle_path, 'rb') as f:
                enc = chardet.detect(f.read())['encoding'] or 'utf-8'

            srt_file = pysrt.open(str(subtitle_path), encoding=enc)

            if len(srt_file) == 0:
                logger.error("No subtitles found in file")
                return []

            total_duration = time_regions(map(srt_segment_to_range, srt_file))
            subtitle_duration = total_duration / len(srt_file)
            n_sentences = max(1, int(duration / subtitle_duration))

            logger.info(f"Processing {len(srt_file)} subtitle entries...")
            summary = summarize(srt_file, min(n_sentences, len(srt_file)))

            return self.optimize_regions(summary, duration)

        except Exception as e:
            logger.error(f"Error processing subtitles: {str(e)}")
            return []

    def optimize_regions(self, regions: List[Tuple[float, float]], target_duration: int) -> List[Tuple[float, float]]:
        """Optimize video regions to match target duration."""
        if not regions:
            return []

        total_duration = sum(end - start for start, end in regions)

        if abs(total_duration - target_duration) <= 5:  # Within 5 seconds tolerance
            return regions

        if total_duration < target_duration:
            # Extend regions proportionally
            ratio = target_duration / total_duration
            optimized = []
            for start, end in regions:
                duration = end - start
                new_duration = duration * ratio
                extension = (new_duration - duration) / 2
                optimized.append((max(0, start - extension), end + extension))
            return optimized
        else:
            # Trim regions to fit target duration
            regions.sort(key=lambda x: x[1] - x[0], reverse=True)
            optimized = []
            current_duration = 0

            for start, end in regions:
                duration = end - start
                if current_duration + duration <= target_duration:
                    optimized.append((start, end))
                    current_duration += duration
                else:
                    remaining = target_duration - current_duration
                    if remaining > 0:
                        optimized.append((start, start + remaining))
                    break

            return sorted(optimized, key=lambda x: x[0])

    def create_summary_video(self, video_path: Path, regions: List[Tuple[float, float]], output_filename: str) -> Optional[Path]:
        """Create summary video from selected regions."""
        try:
            if not regions:
                logger.error("No regions to process")
                return None

            logger.info("Creating video summary...")
            with VideoFileClip(str(video_path)) as video:
                clips = []
                for start, end in regions:
                    try:
                        clip = video.subclip(start, end)
                        clips.append(clip)
                    except Exception as e:
                        logger.warning(
                            f"Failed to process clip {start}-{end}: {str(e)}")
                        continue

                if not clips:
                    logger.error("No valid clips to concatenate")
                    return None

                final_clip = concatenate_videoclips(clips)
                output_path = self.output_dir / output_filename

                logger.info(f"Writing final video to {output_path}")
                final_clip.write_videofile(
                    str(output_path),
                    codec="libx264",
                    audio_codec="aac",
                    temp_audiofile=str(self.temp_dir / "temp_audio.m4a"),
                    remove_temp=True
                )

                return output_path

        except Exception as e:
            logger.error(f"Error creating summary video: {str(e)}")
            return None

    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary files: {str(e)}")

    def process_video(self, url: str, duration: int = 60) -> Optional[Path]:
        """Main processing pipeline."""
        try:
            if not self.check_dependencies():
                return None

            video_path, subtitle_path = self.download_video(url)
            if not video_path or not subtitle_path:
                return None

            regions = self.process_subtitles(subtitle_path, duration)
            if not regions:
                return None

            output_filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            result_path = self.create_summary_video(
                video_path, regions, output_filename)

            self.cleanup()
            return result_path

        except Exception as e:
            logger.error(f"Error in processing pipeline: {str(e)}")
            self.cleanup()
            return None


def main():
    parser = argparse.ArgumentParser(
        description='Create a summary of a YouTube video')
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('--duration', type=int, default=60,
                        help='Target duration of the summary in seconds (default: 60)')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Output directory for the summary video')
    args = parser.parse_args()

    summarizer = VideoSummarizer(output_dir=args.output_dir)
    result_path = summarizer.process_video(args.url, args.duration)

    if result_path:
        print(f"\nSummary video created successfully: {result_path}")
    else:
        print("\nFailed to create summary video. Check the logs for details.")


if __name__ == "__main__":
    main()
