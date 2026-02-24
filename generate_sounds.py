from gtts import gTTS
import os

sounds = {
    "cat_turn": {"text": "miau", "lang": "es"},  # 'es' makes it sound a bit purr-like
    "dog_turn": {"text": "wow", "lang": "en"},
    "cat_win_round": {"text": "Cats win! Miau Miau!", "lang": "en"},
    "dog_win_round": {"text": "Dogs win! Bow wow!", "lang": "en"},
    "cat_win_tournament": {"text": "Meow meow meow meow! The cats have won the tournament!", "lang": "en"},
    "dog_win_tournament": {"text": "Woof woof woof! The dogs are the champions!", "lang": "en"}
}

for name, details in sounds.items():
    tts = gTTS(text=details['text'], lang=details['lang'], slow=False)
    tts.save(f"{name}.mp3")
    print(f"Generated {name}.mp3")
