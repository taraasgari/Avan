from django.core.management.base import BaseCommand

from apps.catalog.models import Product
from apps.experience.models import Challenge, SoloGame


GAMES = [
    {
        "game_type": SoloGame.GameType.RUNNER,
        "slug": "needle-grid",
        "title": "Needle Grid",
        "title_fa": "شبکه سوزن",
        "description": "Pilot a precision needle through a collapsing seam grid. One bad touch can break the run.",
        "description_fa": "سوزن را با دقت از شبکه درزهای متحرک رد کن؛ یک برخورد اشتباه می‌تواند کل ران را خراب کند.",
        "bronze_score": 12000,
        "silver_score": 28000,
        "gold_score": 55000,
        "score_cap": 120000,
        "max_score_per_second": 2200,
        "sort_order": 10,
    },
    {
        "game_type": SoloGame.GameType.CATCH,
        "slug": "pattern-drop",
        "title": "Pattern Drop",
        "title_fa": "سقوط الگو",
        "description": "A high-speed pattern stacker. Rotate, place and clear cutting pieces before the board locks.",
        "description_fa": "الگوهای برش با سرعت بالا سقوط می‌کنند؛ بچرخان، بچین و قبل از قفل شدن صفحه ردیف‌ها را پاک کن.",
        "bronze_score": 8000,
        "silver_score": 20000,
        "gold_score": 45000,
        "score_cap": 100000,
        "max_score_per_second": 1800,
        "sort_order": 20,
    },
    {
        "game_type": SoloGame.GameType.MEMORY,
        "slug": "signal-forge",
        "title": "Signal Forge",
        "title_fa": "کوره سیگنال",
        "description": "Read an accelerating sequence of studio signals and replay it perfectly under pressure.",
        "description_fa": "دنباله‌ای که هر دور سریع‌تر می‌شود حفظ کن و بدون خطا بازسازی‌اش کن.",
        "bronze_score": 7000,
        "silver_score": 18000,
        "gold_score": 40000,
        "score_cap": 90000,
        "max_score_per_second": 1600,
        "sort_order": 30,
    },
    {
        "game_type": SoloGame.GameType.COLOR,
        "slug": "tag-strike",
        "title": "Tag Strike",
        "title_fa": "ضربه تگ",
        "description": "Hit the live AVAN tag before it disappears. Decoys multiply and the timing window keeps shrinking.",
        "description_fa": "تگ واقعی آوان را قبل از ناپدید شدن بزن؛ تگ‌های تقلبی بیشتر می‌شوند و زمان واکنش مدام کمتر می‌شود.",
        "bronze_score": 10000,
        "silver_score": 24000,
        "gold_score": 50000,
        "score_cap": 110000,
        "max_score_per_second": 2000,
        "sort_order": 40,
    },
]


CHALLENGES = [
    {
        "slug": "black-tee-design",
        "title": "Black Tee Challenge",
        "prompt": "Create your strongest graphic for a black AVAN tee.",
        "description": "Build a print that works specifically on a black garment. Contrast and print-readability matter.",
        "challenge_type": "garment",
        "rules": {"garment": "tee", "base_color": "black"},
    },
    {
        "slug": "persian-streetwear",
        "title": "Persian Streetwear",
        "prompt": "Turn Persian visual culture into a modern streetwear graphic.",
        "description": "Use typography, motifs or visual references in an original contemporary composition.",
        "challenge_type": "theme",
        "rules": {"theme": "persian-streetwear"},
    },
    {
        "slug": "two-color-only",
        "title": "Two Colors Only",
        "prompt": "Design a garment graphic using no more than two print colors.",
        "description": "A constraint challenge focused on composition, contrast and restraint.",
        "challenge_type": "limited-colors",
        "rules": {"max_print_colors": 2},
    },
    {
        "slug": "summer-drop-design",
        "title": "Summer Drop",
        "prompt": "Create a design that deserves a place in an AVAN summer drop.",
        "description": "Think wearable, memorable and strong enough to become a real product.",
        "challenge_type": "seasonal",
        "rules": {"season": "summer"},
    },
    {
        "slug": "hoodie-concept",
        "title": "Hoodie Concept",
        "prompt": "Build a hoodie graphic with front, back or sleeve storytelling.",
        "description": "Use the larger hoodie canvas intentionally, especially the back and sleeves.",
        "challenge_type": "garment",
        "rules": {"garment": "hoodie"},
    },
    {
        "slug": "blind-future-tehran",
        "title": "Blind Brief: Future Tehran",
        "prompt": "Future Tehran — 2040. Submit without seeing other entries first.",
        "description": "A blind creative brief. Build your interpretation before comparing it with anyone else.",
        "challenge_type": "blind",
        "rules": {"blind": True, "theme": "future-tehran-2040"},
    },
    {
        "slug": "back-print-only",
        "title": "Back Print Only",
        "prompt": "Create the whole idea using only the back print zone.",
        "description": "No front graphic. Make the back carry the entire story.",
        "challenge_type": "print-zone",
        "rules": {"zones": ["back"]},
    },
    {
        "slug": "sleeve-story",
        "title": "Sleeve Story",
        "prompt": "Build a design where the sleeves are the main visual element.",
        "description": "Treat left and right sleeves as a connected composition.",
        "challenge_type": "print-zone",
        "rules": {"zones": ["left_sleeve", "right_sleeve"]},
    },
    {
        "slug": "one-hour-tee",
        "title": "One Hour Tee",
        "prompt": "Make a complete tee concept from a strict one-hour brief.",
        "description": "A speed-focused design challenge. The owner controls when it is visible and open.",
        "challenge_type": "timed",
        "rules": {"garment": "tee", "suggested_minutes": 60},
    },
]


class Command(BaseCommand):
    help = "Upgrade AVAN PLAY games and seed clothing challenge presets. New challenges stay OFF."

    def handle(self, *args, **options):
        changed_games = 0
        new_challenges = 0

        for data in GAMES:
            game = SoloGame.objects.filter(game_type=data["game_type"]).order_by("id").first()
            if game is None:
                game = SoloGame(game_type=data["game_type"], is_enabled=False)
            for key, value in data.items():
                setattr(game, key, value)
            game.save()
            changed_games += 1

        tee = Product.objects.filter(
            is_active=True,
            studio_profile__is_enabled=True,
            studio_profile__garment_type="tee",
        ).order_by("id").first()
        hoodie = Product.objects.filter(
            is_active=True,
            studio_profile__is_enabled=True,
            studio_profile__garment_type="hoodie",
        ).order_by("id").first()

        for data in CHALLENGES:
            garment = None
            garment_kind = data.get("rules", {}).get("garment")
            if garment_kind == "tee":
                garment = tee
            elif garment_kind == "hoodie":
                garment = hoodie
            _, created = Challenge.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    **data,
                    "garment_product": garment,
                    "status": Challenge.Status.PUBLISHED,
                    "is_enabled": False,
                    "reward_points": 0,
                    "reward_discount_percent": 0,
                    "reward_subsidy_amount": 0,
                },
            )
            new_challenges += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"AVAN PLAY upgraded: {changed_games} game(s) replaced, {new_challenges} new challenge(s) added. New challenges are OFF by default."
        ))
