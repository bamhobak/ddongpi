# -*- coding: utf-8 -*-
"""
게임 속 이모지를 대신하는 아이콘 목록 — tools/gen_icons.py(뽑기)·tools/build_icons.py(시트 만들기)가 함께 쓴다.

NEW   : 새로 뽑는 아이콘 (이모지, 파일이름, 그릴 것)
REUSE : 이미 있는 게임 그림을 그대로 쓰는 이모지 (assets/<파일>.png)
이모지 키에는 변형 선택자(U+FE0F)를 붙이지 않는다 — 게임이 찾을 때 떼고 찾는다.
"""
NEW = [
    # 화면·버튼
    ("⏸", "pause", "a round pause button symbol: two thick rounded vertical bars on a soft sky-blue circular badge"),
    ("🏆", "trophy", "a shiny gold trophy cup with two handles on a small dark base"),
    ("👑", "crown", "a chubby golden crown with three rounded points and small colorful gems"),
    ("✏", "pencil", "a chubby yellow pencil with a pink eraser, tilted diagonally"),
    ("🎵", "music", "two chubby eighth music notes joined by a beam, sky-blue"),
    ("🔔", "bell", "a chubby golden bell with a small clapper"),
    ("🎉", "party", "a party popper cone bursting colorful confetti and curly streamers"),
    ("🥊", "boxing", "a chubby red boxing glove"),
    ("🗼", "tower", "a tall narrow tower made of stacked chocolate-brown soft-serve swirl tiers (a poop tower, NO face) with a tiny red flag on top"),
    ("🔄", "refresh", "two chubby curved arrows chasing each other in a circle (refresh symbol), sky-blue"),
    ("🏠", "home", "a cute small house with a red roof, a round window and a door"),
    ("🔒", "lock", "a chubby golden padlock, closed"),
    ("🔓", "unlock", "a chubby golden padlock with its shackle popped open"),
    ("🔁", "repeat", "two chubby arrows forming a flat loop (repeat symbol), mint green"),
    ("🥇", "gold", "a round gold medal with a red ribbon and a star emblem"),
    ("🥈", "silver", "a round silver medal with a blue ribbon and a star emblem"),
    ("🥉", "bronze", "a round bronze medal with a green ribbon and a star emblem"),
    ("✨", "sparkles", "three sparkly four-pointed stars of different sizes, golden-yellow"),
    ("⚠", "warning", "a chubby rounded yellow warning triangle with a thick dark exclamation mark symbol in it"),
    ("⏱", "stopwatch", "a chubby stopwatch with a button on top, white face with a single red hand"),
    # 직업·펫
    ("🏃", "runner", "a cute running sneaker with speed motion lines"),
    ("🎈", "balloon", "a shiny red balloon with a curly string"),
    ("💪", "muscle", "a cartoon flexed arm showing a big round bicep (arm only)"),
    ("📋", "clipboard", "a clipboard holding a checklist paper with check marks and lines (no readable text)"),
    ("🎯", "target", "a round red-and-white dartboard target with a dart stuck in the bullseye"),
    ("🙏", "pray", "two hands pressed together in prayer"),
    ("🫧", "bubbles", "three shiny iridescent soap bubbles of different sizes"),
    ("🧘", "lotus", "a pink lotus flower"),
    ("🚫", "no", "a red prohibition sign (red circle with a diagonal slash)"),
    ("🦸", "cape", "a flowing red superhero cape with a golden star emblem (cape only, nobody wearing it)"),
    ("⚡", "zap", "a chubby yellow lightning bolt"),
    # 증강
    ("🔥", "fire", "a chubby cartoon flame, orange and yellow"),
    ("🐢", "turtle", "a cute green turtle, side view"),
    ("🐦", "bird", "a small cute sky-blue bird flying"),
    ("📯", "horn", "a golden post horn (curled brass horn)"),
    ("💥", "boom", "a cartoon explosion burst, orange-yellow comic star shape"),
    ("😋", "yum", "a round yellow face savoring delicious food with its tongue out (yum emoji)"),
    ("💉", "syringe", "a cute syringe with pink liquid"),
    ("☔", "rainumbrella", "a blue open umbrella with rain drops falling on it"),
    ("🌠", "shootingstar", "a shooting star: a golden star with a long sparkling trail"),
    ("🕳", "hole", "a dark swirling black hole with a glowing purple ring"),
    ("🌝", "moonface", "a round glowing golden full moon with a gentle smiling face"),
    ("🧲", "magnet", "a red horseshoe magnet with silver tips"),
    ("💨", "fart", "a cute pale-green fart gas cloud puff with swoosh motion lines"),
    ("🍀", "clover", "a four-leaf clover"),
    ("🌧", "raincloud", "a soft grey-blue cloud with rain drops falling"),
    ("💢", "anger", "the red cartoon anger symbol (four curved red marks forming a popping vein cross)"),
    ("🌈", "rainbow", "a chubby rainbow arc with small white clouds at both ends"),
    ("📱", "phone", "a smartphone with a glowing screen showing colorful app icons (no text)"),
    ("🥕", "carrot", "an orange carrot with green leaves"),
    ("🦄", "unicorn", "a cute white unicorn head with a rainbow mane and a golden horn"),
    ("🕰", "clock", "an antique golden mantel clock"),
    ("🎲", "dice", "a white die with dark pips, 3D cube"),
    ("👻", "ghost", "a cute white ghost with a playful face"),
    ("👊", "fist", "a cartoon fist punching forward with a red sleeve cuff"),
    ("👯", "clone", "a rolled ninja scroll with a puff of white smoke (clone jutsu)"),
    # 스테이지·패턴
    ("🍚", "rice", "a bowl of white rice"),
    ("🌀", "swirl", "a blue cyclone swirl spiral"),
    ("🐕", "dog", "a big cute brown dog, side view"),
    ("🎰", "slot", "a slot machine with three reels showing cherries and stars (no text, no numbers)"),
    ("🪜", "ladder", "a wooden ladder"),
    ("🎼", "score", "a musical staff with a treble clef and a few notes"),
    ("✂", "scissors", "a pair of red-handled scissors"),
    # 지대
    ("🌱", "sprout", "a small green sprout with two leaves"),
    ("⛰", "mountain", "a rounded green-brown mountain with a snowy peak"),
    ("☁", "cloud", "a fluffy white cloud"),
    ("🌤", "suncloud", "a golden sun peeking out from behind a white cloud"),
    ("🧊", "ice", "a light-blue ice cube"),
    ("❄", "snowflake", "a chubby light-blue snowflake"),
    ("🛰", "satellite", "a small satellite with blue solar panels"),
    ("🌍", "earth", "the Earth globe with blue oceans and green continents"),
    ("☄", "comet", "a fiery comet with a long glowing tail"),
    ("🌌", "galaxy", "a round night-sky badge showing the purple-blue Milky Way galaxy with stars"),
    ("🌑", "newmoon", "a dark grey new moon disc with faint craters"),
    ("🌒", "darkmoon", "a dark moon with a thin glowing crescent on its right edge"),
    ("⚫", "horizon", "a glossy black orb with a thin glowing orange ring around its edge (black hole event horizon)"),
    ("🧑‍🚀", "astronaut", "a white astronaut helmet with a big glossy blue visor (helmet only, nobody inside)"),
]

REUSE = {"🪙": "item_coin", "⭐": "item_star", "🌙": "item_crescent_moon", "🌕": "item_full_moon",
         "☂": "item_umbrella", "❤": "item_red_heart", "💧": "item_droplet", "🧻": "item_roll_of_paper",
         "🔮": "item_crystal_ball", "💩": "item_poop", "🚀": "pet_galaga", "🕊": "dove",
         "👼": "pet_angel", "🧚": "pet_fairy", "🐈": "pet_cat"}

STYLE = ("This is a small GAME UI ICON drawn at about 24-30 pixels, so it must read clearly: bold simple chunky silhouette, "
         "thick clean soft dark-brown outline, few details, glossy highlight, fills the frame, perfectly centered, front view. "
         "No face on it unless the subject is a creature or the face is the point of the icon. "
         "The reference image is our game's hero puppy — copy ONLY its ART STYLE (kawaii sticker look, clean soft dark-brown "
         "outline, soft glossy pastel shading, rounded chubby shapes); do NOT draw the puppy. Single object only, "
         "transparent background, no text, no letters, no numbers, no ground, no shadow.")
