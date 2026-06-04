import json
import os
import random
from schemas import Scene, VideoScript

_THEMES = {
    "blue": "#0f3460",
    "green": "#1a4a2e",
    "purple": "#2d1b69",
    "dark": "#111111",
}

_EDUCATIONAL_STRUCTURE = [
    ("Introduction", "Welcome to this video about {topic}. Today we will explore key ideas and insights that will help you understand this subject better."),
    ("What Is It?", "{topic} is a fascinating subject that has been growing in importance. It refers to the process and methods used to achieve meaningful outcomes in this area."),
    ("Why It Matters", "Understanding {topic} is more important than ever. It impacts our daily lives and helps us make better decisions in a rapidly changing world."),
    ("Key Concepts", "There are several important concepts to understand about {topic}. These include the core principles, methods, and applications that define this field."),
    ("How It Works", "The process behind {topic} involves several steps. First, we identify the problem. Then we apply the right tools and techniques to find solutions."),
    ("Real World Examples", "We can see {topic} in action all around us. From businesses to everyday life, the applications are vast and growing every day."),
    ("Benefits", "The benefits of {topic} are clear. It saves time, improves outcomes, and opens up new possibilities that were not available before."),
    ("Getting Started", "Getting started with {topic} is easier than you think. Begin with the basics, practice consistently, and you will see progress quickly."),
    ("Summary", "To summarize, {topic} is a powerful concept that offers many benefits. We hope this video has given you a clear understanding of what it is and why it matters."),
    ("Call to Action", "Thank you for watching this video about {topic}. If you found this helpful, please share it with others. Stay curious and keep learning!"),
]

_PROMOTIONAL_STRUCTURE = [
    ("Attention", "Are you struggling with {topic}? You are not alone. Thousands of people face this challenge every day — but there is a solution."),
    ("The Problem", "The old ways of dealing with {topic} are slow, expensive, and frustrating. It is time for a better approach that actually works."),
    ("Introducing", "Introducing our solution for {topic}. Designed for real people, built for real results. Simple, powerful, and effective."),
    ("Key Features", "Our approach to {topic} includes everything you need. Easy to use, proven results, and support every step of the way."),
    ("How It Works", "Getting started with {topic} takes just three simple steps. Sign up, set up your preferences, and start seeing results immediately."),
    ("Social Proof", "Thousands of happy customers have already transformed their experience with {topic}. Join a growing community of success stories."),
    ("Benefits", "With our {topic} solution you will save time, save money, and achieve better results. The advantages speak for themselves."),
    ("Special Offer", "For a limited time, we are offering exclusive access to our {topic} solution. Do not miss this opportunity to change the way you work."),
    ("Call to Action", "Ready to get started with {topic}? Visit our website today, sign up for free, and experience the difference for yourself. Act now!"),
]

_STORYTELLING_STRUCTURE = [
    ("Setting the Scene", "Imagine a world where {topic} changes everything. A world where possibilities are endless and every challenge becomes an opportunity."),
    ("The Beginning", "It all started with a simple question about {topic}. Nobody knew at the time that this question would change everything that followed."),
    ("The Challenge", "The road to mastering {topic} was not easy. There were obstacles, setbacks, and moments of doubt. But every challenge made the journey worthwhile."),
    ("The Discovery", "Then came the breakthrough moment with {topic}. A new perspective, a new approach, and suddenly everything became clear."),
    ("The Turning Point", "Everything changed when the true power of {topic} was revealed. What seemed impossible was now within reach for anyone willing to try."),
    ("The Journey", "The journey through {topic} taught valuable lessons about persistence, creativity, and the importance of never giving up on your goals."),
    ("The Transformation", "Step by step, {topic} transformed what was possible. Results that once took months now happened in days. The impact was undeniable."),
    ("The Outcome", "Today, thanks to {topic}, the story has a happy ending. Goals achieved, lives improved, and a future brighter than ever imagined."),
    ("The Lesson", "The story of {topic} teaches us one powerful lesson — with the right tools and mindset, anything is possible. Your story can start today."),
    ("Inspiration", "So let this story of {topic} inspire you. Take the first step, embrace the journey, and write your own success story starting right now."),
]

_STYLES = {
    "educational": _EDUCATIONAL_STRUCTURE,
    "promotional": _PROMOTIONAL_STRUCTURE,
    "storytelling": _STORYTELLING_STRUCTURE,
}

_VISUALS = [
    "Text on screen with animated icons",
    "Bullet points appearing one by one",
    "Bold headline with supporting graphics",
    "Animated chart or diagram",
    "Split screen with comparison",
    "Full screen text with background",
    "Key words highlighted in color",
    "Simple illustration with caption",
    "Statistics displayed in large font",
    "Quote card with attribution",
]


def _make_title(topic: str, style: str) -> str:
    templates = {
        "educational": f"Understanding {topic.title()} — A Complete Guide",
        "promotional": f"Transform Your Results with {topic.title()}",
        "storytelling": f"The {topic.title()} Story — A Journey of Discovery",
    }
    return templates.get(style, f"{topic.title()} — What You Need to Know")


def generate_video_script(topic: str, style: str, duration: int, theme: str = "blue") -> VideoScript:
    bg_color = _THEMES.get(theme, "#0f3460")
    structure = _STYLES.get(style, _EDUCATIONAL_STRUCTURE)
    num_scenes = max(3, min(len(structure), duration // 12))
    scene_duration = round(duration / num_scenes, 1)

    selected = structure[:num_scenes]
    scenes = []

    for title, narration_template in selected:
        narration = narration_template.format(topic=topic)
        scenes.append(Scene(
            title=title,
            narration=narration,
            visual_description=random.choice(_VISUALS),
            duration=scene_duration,
            background_color=bg_color,
        ))

    return VideoScript(
        title=_make_title(topic, style),
        scenes=scenes,
        total_duration=float(duration),
    )
