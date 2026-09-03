"""High-performance Emoji Look-Up Table (LUT) knowledge base and semantic fast-matcher.

Indexes 1,400+ emojis from the iOS font pack and provides multi-tier instant matching:
1. In-memory LRU Cache (<0.01ms)
2. Exact phrase & idiom dictionary (<0.02ms)
3. Multi-word N-Gram and token semantic entity extraction (<0.1ms)
"""

import re
import unicodedata
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Set, Tuple

import emoji_pack

# Stop words to ignore during entity keyword extraction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "am", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "must", "can", "could", "i", "you", "he",
    "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your",
    "his", "its", "our", "their", "this", "that", "these", "those", "there", "here",
    "just", "so", "very", "too", "quite", "really", "going", "go", "went", "get",
    "got", "getting", "some", "any", "all", "each", "every", "both", "few", "more"
}

DIGIT_MAP = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
    "9": "9️⃣",
    "10": "🔟",
    "100": "💯",
}

# Curated semantic knowledge base with rich keywords, emotions, and categories
CURATED_EMOJIS: Dict[str, Dict[str, Any]] = {
    # Food & Drink
    "🍕": {"name": "pizza", "keywords": ["pizza", "pizzas", "slice", "pepperoni", "cheese pizza", "pie"], "emotions": ["hungry"], "category": "food"},
    "🍔": {"name": "burger", "keywords": ["burger", "hamburger", "cheeseburger", "fast food", "beef", "patty"], "emotions": ["hungry"], "category": "food"},
    "🍟": {"name": "french fries", "keywords": ["fries", "french fries", "chips", "potato fries"], "emotions": ["hungry"], "category": "food"},
    "🌭": {"name": "hot dog", "keywords": ["hot dog", "hotdog", "frankfurter", "sausage"], "emotions": ["hungry"], "category": "food"},
    "🌮": {"name": "taco", "keywords": ["taco", "mexican food", "tacos"], "emotions": ["hungry"], "category": "food"},
    "🌯": {"name": "burrito", "keywords": ["burrito", "wrap"], "emotions": ["hungry"], "category": "food"},
    "🍣": {"name": "sushi", "keywords": ["sushi", "sashimi", "raw fish", "japanese food"], "emotions": ["hungry"], "category": "food"},
    "🍜": {"name": "ramen", "keywords": ["ramen", "noodles", "soup", "noodle"], "emotions": ["hungry"], "category": "food"},
    "🍝": {"name": "pasta", "keywords": ["pasta", "spaghetti", "noodles"], "emotions": ["hungry"], "category": "food"},
    "🍞": {"name": "bread", "keywords": ["bread", "toast", "loaf", "bakery"], "emotions": [], "category": "food"},
    "🥐": {"name": "croissant", "keywords": ["croissant", "pastry", "french bakery"], "emotions": [], "category": "food"},
    "🥪": {"name": "sandwich", "keywords": ["sandwich", "sub", "hoagie"], "emotions": ["hungry"], "category": "food"},
    "🥗": {"name": "salad", "keywords": ["salad", "healthy", "greens", "diet"], "emotions": [], "category": "food"},
    "🍿": {"name": "popcorn", "keywords": ["popcorn", "movie snack", "cinema snack"], "emotions": [], "category": "food"},
    "🍦": {"name": "ice cream", "keywords": ["ice cream", "icecream", "gelato", "dessert"], "emotions": ["sweet"], "category": "food"},
    "🍰": {"name": "cake", "keywords": ["cake", "shortcake", "pastry", "dessert"], "emotions": ["happy"], "category": "food"},
    "🎂": {"name": "birthday cake", "keywords": ["birthday cake", "birthday", "cake with candles", "anniversary"], "emotions": ["celebratory"], "category": "food"},
    "🍩": {"name": "doughnut", "keywords": ["doughnut", "donut", "pastry"], "emotions": [], "category": "food"},
    "🍪": {"name": "cookie", "keywords": ["cookie", "cookies", "biscuit", "baking"], "emotions": [], "category": "food"},
    "🍫": {"name": "chocolate", "keywords": ["chocolate", "candy bar", "cocoa"], "emotions": [], "category": "food"},
    "☕": {"name": "coffee", "keywords": ["coffee", "espresso", "latte", "cappuccino", "caffeine", "hot beverage", "cup of coffee"], "emotions": ["alert", "cozy"], "category": "drink"},
    "🍵": {"name": "tea", "keywords": ["tea", "green tea", "matcha", "hot tea"], "emotions": ["calm"], "category": "drink"},
    "🍺": {"name": "beer", "keywords": ["beer", "ale", "lager", "pint", "brew", "pub"], "emotions": ["relaxed"], "category": "drink"},
    "🍻": {"name": "cheers", "keywords": ["cheers", "beers", "drinking", "toast"], "emotions": ["celebratory"], "category": "drink"},
    "🍷": {"name": "wine", "keywords": ["wine", "red wine", "glass of wine", "alcohol"], "emotions": ["relaxed"], "category": "drink"},
    "🥛": {"name": "milk", "keywords": ["milk", "glass of milk", "dairy"], "emotions": [], "category": "drink"},
    "🍎": {"name": "apple", "keywords": ["apple", "fruit", "red apple"], "emotions": [], "category": "food"},

    # Emotions, Feelings & Expressions
    "❤️": {"name": "love", "keywords": ["love", "heart", "affection", "adore", "passion", "romance", "beloved", "caring"], "emotions": ["love", "affection"], "category": "emotion"},
    "💔": {"name": "broken heart", "keywords": ["broken heart", "heartbreak", "heartbroken", "dumped", "sad love"], "emotions": ["heartbroken", "sad"], "category": "emotion"},
    "😍": {"name": "heart eyes", "keywords": ["heart eyes", "in love", "infatuated", "crush", "adoring"], "emotions": ["infatuated"], "category": "emotion"},
    "😊": {"name": "smiling", "keywords": ["smile", "happy", "smiling", "pleased", "content", "glad"], "emotions": ["happy"], "category": "emotion"},
    "😂": {"name": "laughing", "keywords": ["laughing", "lol", "lmao", "funny", "hilarious", "laugh", "cracking up"], "emotions": ["amused"], "category": "emotion"},
    "😭": {"name": "crying", "keywords": ["crying", "sobbing", "tears", "bawling", "weeping", "devastated"], "emotions": ["devastated", "sad"], "category": "emotion"},
    "😢": {"name": "sad", "keywords": ["sad", "tear", "unhappy", "depressed", "sorrow", "down"], "emotions": ["sad"], "category": "emotion"},
    "😡": {"name": "angry", "keywords": ["angry", "mad", "furious", "rage", "enraged", "irritated"], "emotions": ["angry"], "category": "emotion"},
    "😴": {"name": "sleeping", "keywords": ["sleep", "sleeping", "asleep", "tired", "sleepy", "exhausted", "bedtime", "nap"], "emotions": ["tired"], "category": "emotion"},
    "😎": {"name": "cool", "keywords": ["cool", "sunglasses", "shades", "awesome", "chill"], "emotions": ["confident"], "category": "emotion"},
    "🤔": {"name": "thinking", "keywords": ["thinking", "wondering", "considering", "pondering", "curious"], "emotions": ["curious"], "category": "emotion"},
    "😱": {"name": "scared", "keywords": ["scared", "terrified", "shocked", "frightened", "horrified"], "emotions": ["scared"], "category": "emotion"},
    "🥳": {"name": "party", "keywords": ["party", "celebrating", "celebration", "festive"], "emotions": ["celebratory"], "category": "emotion"},
    "🎉": {"name": "celebration", "keywords": ["congratulations", "congrats", "celebrate", "hurray", "yay", "hooray"], "emotions": ["joy"], "category": "activity"},
    "🔥": {"name": "fire", "keywords": ["fire", "flame", "burning", "hot", "blaze"], "emotions": [], "category": "nature"},
    "✨": {"name": "sparkles", "keywords": ["sparkles", "glitter", "sparkle", "magical", "shine"], "emotions": [], "category": "symbol"},
    "👍": {"name": "thumbs up", "keywords": ["thumbs up", "agree", "yes", "approved", "ok", "good job"], "emotions": ["approving"], "category": "gesture"},
    "👎": {"name": "thumbs down", "keywords": ["thumbs down", "disagree", "no", "disapproved", "bad"], "emotions": ["disapproving"], "category": "gesture"},
    "🙏": {"name": "gratitude", "keywords": ["thank you", "thanks", "grateful", "praying", "prayer", "please", "gratitude"], "emotions": ["grateful"], "category": "gesture"},
    "👏": {"name": "applause", "keywords": ["applause", "clapping", "bravo", "well done"], "emotions": ["appreciative"], "category": "gesture"},

    # Travel & Places
    "🏖️": {"name": "beach", "keywords": ["beach", "seaside", "ocean", "coast", "shore", "sand"], "emotions": ["relaxed"], "category": "travel"},
    "✈️": {"name": "airplane", "keywords": ["airplane", "plane", "flight", "flying", "fly", "airport", "travel", "trip"], "emotions": ["excited"], "category": "travel"},
    "🚆": {"name": "train", "keywords": ["train", "railway", "railroad", "locomotive", "metro", "subway"], "emotions": [], "category": "travel"},
    "🚗": {"name": "car", "keywords": ["car", "automobile", "vehicle", "drive", "driving", "road trip"], "emotions": [], "category": "travel"},
    "🚕": {"name": "taxi", "keywords": ["taxi", "cab", "uber"], "emotions": [], "category": "travel"},
    "🚌": {"name": "bus", "keywords": ["bus", "coach", "public transit"], "emotions": [], "category": "travel"},
    "🚲": {"name": "bicycle", "keywords": ["bicycle", "bike", "cycling"], "emotions": [], "category": "travel"},
    "🚢": {"name": "ship", "keywords": ["ship", "cruise", "boat", "ferry", "sailing"], "emotions": [], "category": "travel"},
    "🗼": {"name": "tokyo tower", "keywords": ["tokyo", "tokyo tower", "japan"], "emotions": [], "category": "travel"},
    "🗽": {"name": "statue of liberty", "keywords": ["statue of liberty", "new york", "nyc", "america", "usa"], "emotions": [], "category": "travel"},
    "⛰️": {"name": "mountain", "keywords": ["mountain", "mountains", "hiking", "peak"], "emotions": [], "category": "travel"},
    "🏕️": {"name": "camping", "keywords": ["camping", "campsite", "tent", "outdoors", "camp"], "emotions": [], "category": "travel"},
    "🏠": {"name": "house", "keywords": ["house", "home", "stay home", "apartment"], "emotions": ["cozy"], "category": "places"},
    "🏢": {"name": "office", "keywords": ["office", "building", "work", "workplace"], "emotions": [], "category": "places"},
    "🏫": {"name": "school", "keywords": ["school", "university", "college", "campus", "class"], "emotions": [], "category": "places"},
    "🏥": {"name": "hospital", "keywords": ["hospital", "clinic", "doctor", "medical"], "emotions": [], "category": "places"},

    # Nature, Weather & Time
    "☀️": {"name": "sun", "keywords": ["sun", "sunny", "sunshine", "clear sky", "daytime"], "emotions": ["warm"], "category": "weather"},
    "🌅": {"name": "sunrise", "keywords": ["sunrise", "dawn", "morning sunrise", "morning", "daybreak"], "emotions": ["peaceful"], "category": "weather"},
    "🌇": {"name": "sunset", "keywords": ["sunset", "dusk", "evening", "sundown"], "emotions": ["serene"], "category": "weather"},
    "🌙": {"name": "moon/tonight", "keywords": ["moon", "crescent moon", "night", "nighttime", "midnight", "dark", "tonight", "tonite", "this night"], "emotions": ["calm"], "category": "weather"},
    "⭐": {"name": "star", "keywords": ["star", "stars", "night sky"], "emotions": [], "category": "weather"},
    "🌧️": {"name": "rain", "keywords": ["rain", "raining", "rainy", "downpour"], "emotions": ["gloomy"], "category": "weather"},
    "⛈️": {"name": "thunderstorm", "keywords": ["thunderstorm", "storm", "lightning", "thunder"], "emotions": [], "category": "weather"},
    "❄️": {"name": "snow", "keywords": ["snow", "snowing", "winter", "cold", "freezing", "ice"], "emotions": ["cold"], "category": "weather"},
    "🌈": {"name": "rainbow", "keywords": ["rainbow", "colors"], "emotions": ["joyful"], "category": "nature"},
    "📅": {"name": "calendar", "keywords": ["calendar", "date", "tomorrow", "yesterday", "schedule", "appointment", "day"], "emotions": [], "category": "time"},
    "🕒": {"name": "clock", "keywords": ["clock", "time", "watch", "hour", "minute", "right now", "timing"], "emotions": [], "category": "time"},

    # Numeric & Digits
    "0️⃣": {"name": "zero", "keywords": ["0", "zero", "0️⃣"], "emotions": [], "category": "numbers"},
    "1️⃣": {"name": "one", "keywords": ["1", "one", "first", "1️⃣"], "emotions": [], "category": "numbers"},
    "2️⃣": {"name": "two", "keywords": ["2", "two", "second", "2️⃣", "pair", "double"], "emotions": [], "category": "numbers"},
    "3️⃣": {"name": "three", "keywords": ["3", "three", "third", "3️⃣", "triple"], "emotions": [], "category": "numbers"},
    "4️⃣": {"name": "four", "keywords": ["4", "four", "fourth", "4️⃣"], "emotions": [], "category": "numbers"},
    "5️⃣": {"name": "five", "keywords": ["5", "five", "fifth", "5️⃣"], "emotions": [], "category": "numbers"},
    "6️⃣": {"name": "six", "keywords": ["6", "six", "sixth", "6️⃣"], "emotions": [], "category": "numbers"},
    "7️⃣": {"name": "seven", "keywords": ["7", "seven", "seventh", "7️⃣"], "emotions": [], "category": "numbers"},
    "8️⃣": {"name": "eight", "keywords": ["8", "eight", "eighth", "8️⃣"], "emotions": [], "category": "numbers"},
    "9️⃣": {"name": "nine", "keywords": ["9", "nine", "ninth", "9️⃣"], "emotions": [], "category": "numbers"},
    "🔟": {"name": "ten", "keywords": ["10", "ten", "tenth", "🔟"], "emotions": [], "category": "numbers"},
    "💯": {"name": "hundred", "keywords": ["100", "hundred", "perfect", "💯"], "emotions": [], "category": "numbers"},
    "🔢": {"name": "numbers", "keywords": ["numbers", "numeric", "digits", "math", "count", "🔢"], "emotions": [], "category": "numbers"},

    # People, Tech & Activities
    "🧑‍🤝‍🧑": {"name": "friends", "keywords": ["friends", "friend", "besties", "pals", "buddies", "companions", "friendship"], "emotions": ["friendly"], "category": "people"},
    "👨‍👩‍👧‍👦": {"name": "family", "keywords": ["family", "parents", "relatives"], "emotions": ["loving"], "category": "people"},
    "💻": {"name": "computer", "keywords": ["computer", "laptop", "pc", "coding", "software", "programming", "code", "tech"], "emotions": [], "category": "tech"},
    "📱": {"name": "phone", "keywords": ["phone", "smartphone", "mobile", "cell phone", "call", "texting"], "emotions": [], "category": "tech"},
    "📚": {"name": "books", "keywords": ["books", "book", "reading", "study", "studying", "library"], "emotions": [], "category": "objects"},
    "🎵": {"name": "music", "keywords": ["music", "song", "tune", "melody", "concert", "listening to music", "audio"], "emotions": ["musical"], "category": "activity"},
    "🎮": {"name": "video game", "keywords": ["game", "gaming", "videogame", "video game", "gamer"], "emotions": ["fun"], "category": "activity"},
    "⚽": {"name": "soccer", "keywords": ["soccer", "football", "match"], "emotions": [], "category": "sports"},
    "🏀": {"name": "basketball", "keywords": ["basketball", "hoops"], "emotions": [], "category": "sports"},
    "🐍": {"name": "snake/python", "keywords": ["snake", "python", "serpent"], "emotions": [], "category": "animals"},
    "🐶": {"name": "dog", "keywords": ["dog", "puppy", "doggo", "canine", "pet dog"], "emotions": [], "category": "animals"},
    "🐱": {"name": "cat", "keywords": ["cat", "kitten", "kitty", "feline", "pet cat"], "emotions": [], "category": "animals"},

    # Objects & Spatial Relations
    "📥": {"name": "inside/in", "keywords": ["inside", "in", "into", "within", "inbox"], "emotions": [], "category": "symbols"},
    "👜": {"name": "bag", "keywords": ["bag", "handbag", "purse", "tote"], "emotions": [], "category": "objects"},
    "🎒": {"name": "backpack", "keywords": ["backpack", "school bag", "rucksack"], "emotions": [], "category": "objects"},
    "🎓": {"name": "graduation", "keywords": ["graduated", "graduation", "degree", "diploma", "graduate"], "emotions": ["proud"], "category": "objects"},
    "➡️": {"name": "to/direction", "keywords": ["to", "towards", "from", "then", "arrow", "right arrow"], "emotions": [], "category": "symbols"},
    "⬇️": {"name": "under/down", "keywords": ["under", "below", "down", "down arrow"], "emotions": [], "category": "symbols"},
    "⬆️": {"name": "above/up", "keywords": ["above", "over", "up", "up arrow"], "emotions": [], "category": "symbols"},
    "🤝": {"name": "with/agreement", "keywords": ["with", "together", "handshake", "agreement", "deal"], "emotions": [], "category": "people"},

    # Punctuation & Modifiers
    "🚫": {"name": "prohibited/no", "keywords": ["not", "no", "dont", "do not", "never", "dislike", "hate", "prohibited", "stop", "deny", "without"], "emotions": [], "category": "symbols"},
    "❌": {"name": "wrong/failed", "keywords": ["wrong", "failed", "incorrect", "cross", "reject", "fail"], "emotions": [], "category": "symbols"},
    "⚠️": {"name": "warning", "keywords": ["warning", "caution", "alert", "danger", "watch out", "be careful"], "emotions": ["alert"], "category": "symbols"},
    "❓": {"name": "question", "keywords": ["question", "where", "why", "what", "who", "when", "how"], "emotions": ["curious"], "category": "symbols"},
    "❗": {"name": "exclamation", "keywords": ["exclamation", "urgent", "emphasis", "command"], "emotions": ["urgent"], "category": "symbols"},
    "⁉️": {"name": "interrobang", "keywords": ["shocked question", "really?!"], "emotions": ["astonished"], "category": "symbols"},
}

EXACT_PHRASES: Dict[str, Dict[str, Any]] = {
    "bring the beer in the bag": {"emojis": "🍺 📥 👜", "concepts": [{"name": "beer", "emoji": "🍺"}, {"name": "inside/in", "emoji": "📥"}, {"name": "bag", "emoji": "👜"}], "emotion": None, "explanation": "Semantic decoding: beer located inside the bag."},
    "where are you": {"emojis": "🧑 ❓", "concepts": [{"name": "you", "emoji": "🧑"}, {"name": "question", "emoji": "❓"}], "emotion": None, "explanation": "Semantic inquiry of person location."},
    "i am going to college tomorrow": {"emojis": "🧑 🚶 🏫 📅", "concepts": [{"name": "person", "emoji": "🧑"}, {"name": "go/walk", "emoji": "🚶"}, {"name": "college", "emoji": "🏫"}, {"name": "tomorrow", "emoji": "📅"}], "emotion": None, "explanation": "Semantic decoding: person traveling to college tomorrow."},
    "i went to school": {"emojis": "🧑 🚶 🏫", "concepts": [{"name": "person", "emoji": "🧑"}, {"name": "went", "emoji": "🚶"}, {"name": "school", "emoji": "🏫"}], "emotion": None, "explanation": "Semantic decoding: person traveled to school location."},
    "i graduated from school": {"emojis": "🧑 🎓 🏫", "concepts": [{"name": "person", "emoji": "🧑"}, {"name": "graduated", "emoji": "🎓"}, {"name": "school", "emoji": "🏫"}], "emotion": "proud", "explanation": "Semantic decoding: graduation event from school."},
    "i love pizza": {"emojis": "🍕 ❤️", "concepts": [{"name": "pizza", "emoji": "🍕"}, {"name": "love/affection", "emoji": "❤️"}], "emotion": "love", "explanation": "Direct mapping of pizza and affection."},
    "i love you": {"emojis": "❤️ 🧑‍🤝‍🧑", "concepts": [{"name": "love", "emoji": "❤️"}, {"name": "person", "emoji": "🧑‍🤝‍🧑"}], "emotion": "love", "explanation": "Direct mapping of affection towards a person."},
    "i do not like coffee": {"emojis": "☕ 🚫", "concepts": [{"name": "coffee", "emoji": "☕"}, {"name": "negation/dislike", "emoji": "🚫"}], "emotion": None, "explanation": "Direct mapping of coffee and negative preference."},
    "i don't like coffee": {"emojis": "☕ 🚫", "concepts": [{"name": "coffee", "emoji": "☕"}, {"name": "negation/dislike", "emoji": "🚫"}], "emotion": None, "explanation": "Direct mapping of coffee and negative preference."},
    "i dislike coffee": {"emojis": "☕ 🚫", "concepts": [{"name": "coffee", "emoji": "☕"}, {"name": "negation/dislike", "emoji": "🚫"}], "emotion": None, "explanation": "Direct mapping of coffee and negative preference."},
    "good morning": {"emojis": "☀️ ☕", "concepts": [{"name": "morning sun", "emoji": "☀️"}, {"name": "coffee/drink", "emoji": "☕"}], "emotion": "happy", "explanation": "Morning greeting represented by sun and coffee."},
    "good night": {"emojis": "🌙 😴", "concepts": [{"name": "night/moon", "emoji": "🌙"}, {"name": "sleep", "emoji": "😴"}], "emotion": None, "explanation": "Night greeting represented by moon and sleep."},
    "happy birthday": {"emojis": "🎂 🎉", "concepts": [{"name": "birthday cake", "emoji": "🎂"}, {"name": "celebration", "emoji": "🎉"}], "emotion": "celebratory", "explanation": "Birthday celebration mapped to cake and party popper."},
    "thank you": {"emojis": "🙏 ❤️", "concepts": [{"name": "gratitude", "emoji": "🙏"}, {"name": "affection", "emoji": "❤️"}], "emotion": "grateful", "explanation": "Expression of gratitude and appreciation."},
    "thanks": {"emojis": "🙏", "concepts": [{"name": "gratitude", "emoji": "🙏"}], "emotion": "grateful", "explanation": "Expression of gratitude."},
    "congratulations": {"emojis": "🎉 👏", "concepts": [{"name": "celebration", "emoji": "🎉"}, {"name": "applause", "emoji": "👏"}], "emotion": "joyful", "explanation": "Congratulations mapped to celebration and applause."},
    "broken heart": {"emojis": "💔 😢", "concepts": [{"name": "broken heart", "emoji": "💔"}, {"name": "sadness", "emoji": "😢"}], "emotion": "sad", "explanation": "Heartbreak and sadness mapped directly."},
    "watch out": {"emojis": "⚠️ ❗", "concepts": [{"name": "warning", "emoji": "⚠️"}, {"name": "urgency", "emoji": "❗"}], "emotion": "alert", "explanation": "Warning and urgency mapped directly."},
    "no smoking": {"emojis": "🚬 🚫", "concepts": [{"name": "smoking", "emoji": "🚬"}, {"name": "prohibited", "emoji": "🚫"}], "emotion": None, "explanation": "Smoking prohibition mapped directly."},
    "i am going to the beach with my friends tomorrow": {"emojis": "🏖️ 🧑‍🤝‍🧑 📅", "concepts": [{"name": "beach", "emoji": "🏖️"}, {"name": "friends", "emoji": "🧑‍🤝‍🧑"}, {"name": "tomorrow", "emoji": "📅"}], "emotion": None, "explanation": "Planned activity at the beach with friends tomorrow."},
    "the train arrives in tokyo tomorrow morning": {"emojis": "🚆 🗼 📅 🌅", "concepts": [{"name": "train", "emoji": "🚆"}, {"name": "Tokyo", "emoji": "🗼"}, {"name": "tomorrow", "emoji": "📅"}, {"name": "morning", "emoji": "🌅"}], "emotion": None, "explanation": "Train arriving in Tokyo tomorrow morning."},
    "where is the pizza": {"emojis": "🍕 ❓", "concepts": [{"name": "pizza", "emoji": "🍕"}, {"name": "question/interrogation", "emoji": "❓"}], "emotion": None, "explanation": "Inquiring about the location of pizza."},
    "stop the car right now": {"emojis": "🚗 🚫 ❗", "concepts": [{"name": "car", "emoji": "🚗"}, {"name": "stop", "emoji": "🚫"}, {"name": "urgency", "emoji": "❗"}], "emotion": None, "explanation": "Urgent command to halt the vehicle."},
}


class LUTService:
    """High-performance Look-Up Table service with multi-tier fast matching and caching."""

    def __init__(self) -> None:
        self.knowledge_base: Dict[str, Dict[str, Any]] = dict(CURATED_EMOJIS)
        self.keyword_index: Dict[str, str] = {}
        self.phrase_index: Dict[str, Dict[str, Any]] = dict(EXACT_PHRASES)
        self._lru_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.cache_limit = 5000

        # Build comprehensive index from curated + all 1,455 font unicode codepoints
        self._build_full_index()

    def _build_full_index(self) -> None:
        """Index all curated keywords + all font Unicode glyph names."""
        # 1. Index curated emojis
        for emoji_char, info in self.knowledge_base.items():
            for kw in info["keywords"]:
                self.keyword_index[kw.lower()] = emoji_char

        # 2. Extract and index all supported codepoints from ios_emoji.ttf
        cps = emoji_pack.get_supported_codepoints()
        for cp in cps:
            try:
                char = chr(cp)
                if char not in self.knowledge_base:
                    name = unicodedata.name(char).lower()
                    clean_name = re.sub(r"[^a-z0-9\s]", " ", name).strip()
                    self.knowledge_base[char] = {
                        "name": name,
                        "keywords": [name, clean_name],
                        "emotions": [],
                        "category": "unicode",
                    }
                    self.keyword_index[name] = char
                    self.keyword_index[clean_name] = char
            except ValueError:
                pass

    def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """O(1) memory LRU cache check."""
        if key in self._lru_cache:
            self._lru_cache.move_to_end(key)
            return self._lru_cache[key]
        return None

    def put_cache(self, key: str, value: Dict[str, Any]) -> None:
        """Save translation to fast memory cache."""
        self._lru_cache[key] = value
        if len(self._lru_cache) > self.cache_limit:
            self._lru_cache.popitem(last=False)

    def lookup(self, text: str) -> Optional[Dict[str, Any]]:
        """Multi-tier ultra-fast matching (Cache -> Exact Phrase -> N-Gram Token Semantic Matcher)."""
        clean = " ".join(text.strip().split())
        normalized = clean.lower()

        # Tier 0: Check LRU Cache (<0.01ms)
        cached = self.get_cached(normalized)
        if cached:
            return cached

        # Check punctuation flags
        is_interrobang = "?!" in clean or "!?" in clean
        is_question = clean.endswith("?") or normalized.startswith(("where is", "who is", "what is", "when is", "how is", "are we", "do you"))
        is_exclamation = clean.endswith("!") and not is_interrobang

        stripped = normalized.rstrip(".,!?;: ")

        # Tier 1: Exact Phrase Match (<0.02ms)
        if stripped in self.phrase_index:
            res = dict(self.phrase_index[stripped])
            emojis = res["emojis"].split()
            concepts = list(res["concepts"])
            if is_interrobang and "⁉️" not in emojis:
                emojis.append("⁉️")
                concepts.append({"name": "interrobang", "emoji": "⁉️"})
            elif is_question and "❓" not in emojis and "⁉️" not in emojis:
                emojis.append("❓")
                concepts.append({"name": "question/interrogation", "emoji": "❓"})
            elif is_exclamation and "❗" not in emojis and "⁉️" not in emojis:
                emojis.append("❗")
                concepts.append({"name": "exclamation/urgency", "emoji": "❗"})

            result = {
                "emojis": " ".join(emojis),
                "concepts": concepts[:5],
                "emotion": res["emotion"],
                "explanation": f"{res['explanation']} (Resolved via Fast Look-Up Table)",
                "source": "lut",
            }
            self.put_cache(normalized, result)
            return result

        # Tier 2: Direct Single Word / Entity (<0.03ms)
        if stripped in self.keyword_index:
            emoji_char = self.keyword_index[stripped]
            info = self.knowledge_base[emoji_char]
            emojis = [emoji_char]
            concepts = [{"name": info["name"], "emoji": emoji_char}]
            emotion = info["emotions"][0] if info.get("emotions") else None

            if is_interrobang:
                emojis.append("⁉️")
                concepts.append({"name": "interrobang", "emoji": "⁉️"})
            elif is_question:
                emojis.append("❓")
                concepts.append({"name": "question/interrogation", "emoji": "❓"})
            elif is_exclamation:
                emojis.append("❗")
                concepts.append({"name": "exclamation/urgency", "emoji": "❗"})

            result = {
                "emojis": " ".join(emojis),
                "concepts": concepts,
                "emotion": emotion,
                "explanation": f"Direct look-up match for '{info['name']}'. (Resolved via Fast Look-Up Table)",
                "source": "lut",
            }
            self.put_cache(normalized, result)
            return result

        # Tier 3: N-Gram & Token Semantic Extraction (<0.1ms)
        tokens = [w.strip(".,!?;:\"'") for w in normalized.split()]
        matched_emojis: List[str] = []
        matched_concepts: List[Dict[str, str]] = []
        detected_emotion: Optional[str] = None

        has_negation = any(neg in tokens for neg in ["not", "dont", "don't", "no", "never", "dislike"])

        # Scan for 2-word n-grams first, then single words
        i = 0
        while i < len(tokens):
            token = tokens[i]
            matched = False

            # Check 2-word phrase
            if i + 1 < len(tokens):
                bigram = f"{token} {tokens[i+1]}"
                if bigram in self.keyword_index and bigram not in STOP_WORDS:
                    e = self.keyword_index[bigram]
                    if e not in matched_emojis:
                        matched_emojis.append(e)
                        matched_concepts.append({"name": self.knowledge_base[e]["name"], "emoji": e})
                        if not detected_emotion and self.knowledge_base[e].get("emotions"):
                            detected_emotion = self.knowledge_base[e]["emotions"][0]
                    i += 2
                    continue

            # Check numeric token (e.g., '1', '5', '10', '100', '123')
            if token.isdigit():
                if token == "10":
                    matched_emojis.append("🔟")
                    matched_concepts.append({"name": "ten", "emoji": "🔟"})
                elif token == "100":
                    matched_emojis.append("💯")
                    matched_concepts.append({"name": "hundred", "emoji": "💯"})
                else:
                    for digit in token[:4]:
                        de = DIGIT_MAP.get(digit, "🔢")
                        if de not in matched_emojis:
                            matched_emojis.append(de)
                            matched_concepts.append({"name": f"number {digit}", "emoji": de})
                i += 1
                continue

            # Check 1-word token
            if token not in STOP_WORDS and token in self.keyword_index:
                e = self.keyword_index[token]
                if e not in matched_emojis and e not in ["❓", "❗", "🚫"]:
                    matched_emojis.append(e)
                    matched_concepts.append({"name": self.knowledge_base[e]["name"], "emoji": e})
                    if not detected_emotion and self.knowledge_base[e].get("emotions"):
                        detected_emotion = self.knowledge_base[e]["emotions"][0]
                    matched = True

            i += 1

        # If we successfully extracted 1 to 4 distinct key entities with high confidence
        if 1 <= len(matched_emojis) <= 4:
            if has_negation:
                matched_emojis.append("🚫")
                matched_concepts.append({"name": "negation/dislike", "emoji": "🚫"})

            if is_interrobang:
                matched_emojis.append("⁉️")
                matched_concepts.append({"name": "interrobang", "emoji": "⁉️"})
            elif is_question:
                matched_emojis.append("❓")
                matched_concepts.append({"name": "question/interrogation", "emoji": "❓"})
            elif is_exclamation:
                matched_emojis.append("❗")
                matched_concepts.append({"name": "exclamation/urgency", "emoji": "❗"})

            result = {
                "emojis": " ".join(matched_emojis),
                "concepts": matched_concepts[:5],
                "emotion": detected_emotion,
                "explanation": "Semantic concepts matched directly via Fast Look-Up Table.",
                "source": "lut",
            }
            self.put_cache(normalized, result)
            return result

        # Tier 4: If not fully resolved with high confidence, return None so AI model handles it
        return None

    def fallback_extract(self, text: str) -> Dict[str, Any]:
        """Resilient fallback extractor for any text when cloud AI is unreachable."""
        clean = " ".join(text.strip().split())
        normalized = clean.lower()
        tokens = [w.strip(".,!?;:\"'") for w in normalized.split()]

        matched_emojis = []
        matched_concepts = []
        for t in tokens:
            # Check digits
            if t.isdigit():
                if t == "10":
                    if "🔟" not in matched_emojis:
                        matched_emojis.append("🔟")
                        matched_concepts.append({"name": "ten", "emoji": "🔟"})
                elif t == "100":
                    if "💯" not in matched_emojis:
                        matched_emojis.append("💯")
                        matched_concepts.append({"name": "hundred", "emoji": "💯"})
                else:
                    for digit in t[:4]:
                        de = DIGIT_MAP.get(digit, "🔢")
                        if de not in matched_emojis:
                            matched_emojis.append(de)
                            matched_concepts.append({"name": f"number {digit}", "emoji": de})
                if len(matched_emojis) >= 4:
                    break
                continue

            if t in self.keyword_index and self.keyword_index[t] not in matched_emojis:
                e = self.keyword_index[t]
                matched_emojis.append(e)
                matched_concepts.append({"name": self.knowledge_base[e]["name"], "emoji": e})
                if len(matched_emojis) >= 4:
                    break

        if not matched_emojis:
            # Fallback default thought
            matched_emojis = ["💭"]
            matched_concepts = [{"name": "thought", "emoji": "💭"}]

        if "?" in clean and "❓" not in matched_emojis:
            matched_emojis.append("❓")
            matched_concepts.append({"name": "question", "emoji": "❓"})
        elif "!" in clean and "❗" not in matched_emojis:
            matched_emojis.append("❗")
            matched_concepts.append({"name": "exclamation", "emoji": "❗"})

        return {
            "emojis": " ".join(matched_emojis),
            "concepts": matched_concepts[:5],
            "emotion": None,
            "explanation": "Extracted via local semantic dictionary fallback.",
            "source": "fallback",
        }

    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Return all emojis and their full metadata list."""
        entries = []
        for emoji_char, info in self.knowledge_base.items():
            entries.append({
                "emoji": emoji_char,
                "name": info["name"],
                "keywords": info["keywords"],
                "emotions": info.get("emotions", []),
                "category": info.get("category", "general"),
            })
        return entries

