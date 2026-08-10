import io
import json
import random
import urllib.error
import urllib.parse
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from PIL import Image, ImageDraw, ImageFont, ImageOps

from products.models import Category, Product, ProductImage, Variant

SEED_MARKER = '[seed_products demo item]'

USER_AGENT = 'ELINK-DemoSeeder/1.0 (local dev catalog seeding)'

# Categories backed by DummyJSON (https://dummyjson.com) - a public demo/prototyping
# API purpose-built for e-commerce mockups, with real curated product photos (no
# scraping, no licensing risk, no relevance/safety roulette like generic image search).
# Each entry lists which DummyJSON sub-categories to pull real products from.
DUMMYJSON_PLAN = {
    'Accessories': [('sunglasses', 4), ('womens-bags', 3), ('womens-watches', 3)],
    'Electronics': [('smartphones', 4), ('laptops', 3), ('tablets', 3)],
    'Fashion': [('tops', 2), ('mens-shirts', 2), ('womens-dresses', 2), ('mens-shoes', 2), ('womens-shoes', 2)],
    'Home & Kitchen': [('kitchen-accessories', 6), ('home-decoration', 2), ('furniture', 2)],
    'Other': [('sports-accessories', 3), ('groceries', 2), ('fragrances', 2), ('beauty', 2), ('motorcycle', 1)],
}

# DummyJSON has no baby/kids or hand-tools categories, so those two are still
# generated (adjective + noun) with a single hand-picked, manually safety- and
# relevance-checked real photo per noun (see NOUN_PHOTO_URL below). Every URL in
# that dict was visually verified - do not swap in unverified search results here,
# a prior pass using automated keyword image search surfaced actual explicit
# content that slipped past the API's own safety filter.
CATEGORY_WORDS = {
    'Baby & Kids': (['Soft', 'Organic Cotton', 'BPA-Free', 'Non-Toxic', 'Padded', 'Washable'],
                    ['Onesie', 'Stroller', 'Baby Monitor', 'Highchair', 'Diaper Bag', 'Teething Toy', 'Crib Sheet']),
    'Tools': (['Heavy-Duty', 'Cordless', 'Precision', 'Rust-Resistant', 'Professional'],
              ['Drill', 'Wrench Set', 'Hammer', 'Screwdriver Kit', 'Tool Box', 'Measuring Tape']),
}

# noun -> verified direct photo URL, or None to always use the placeholder.
NOUN_PHOTO_URL = {
    'Onesie': 'https://live.staticflickr.com/8018/7294603390_3fac269343_b.jpg',
    'Stroller': 'https://live.staticflickr.com/1135/1354541640_a4b8d2a2a3_b.jpg',
    'Baby Monitor': 'https://live.staticflickr.com/3035/2752064495_2d48686623_b.jpg',
    'Highchair': 'https://live.staticflickr.com/8145/7558433470_dfe11d6ec2.jpg',
    'Diaper Bag': 'https://live.staticflickr.com/6150/5924342745_d9ba382845_b.jpg',
    'Teething Toy': 'https://live.staticflickr.com/3899/14674808509_e0cffb5b2f_b.jpg',
    'Crib Sheet': 'https://live.staticflickr.com/6233/6378887417_b6376cf991_m.jpg',
    'Drill': 'https://live.staticflickr.com/8372/8559707469_3b5c87b53b_b.jpg',
    'Wrench Set': 'https://live.staticflickr.com/8086/8559723017_df552e009b_b.jpg',
    'Hammer': 'https://upload.wikimedia.org/wikipedia/commons/4/49/Carpenter%27s_hammer.JPG',
    'Screwdriver Kit': 'https://live.staticflickr.com/2789/4150696778_ae7a2afd01_b.jpg',
    'Tool Box': 'https://live.staticflickr.com/65535/49921066491_04332083c0_b.jpg',
    'Measuring Tape': 'https://live.staticflickr.com/65535/49902401051_5b91528940_b.jpg',
}

CATEGORY_COLORS = {
    'Accessories': (146, 64, 14),
    'Baby & Kids': (219, 39, 119),
    'Electronics': (14, 116, 144),
    'Fashion': (99, 102, 241),
    'Home & Kitchen': (217, 119, 6),
    'Other': (71, 85, 105),
    'Tools': (55, 65, 81),
}
FALLBACK_COLOR = (10, 133, 99)


def _get(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()


def to_square_jpeg(raw_bytes):
    img = Image.open(io.BytesIO(raw_bytes))
    img = ImageOps.exif_transpose(img).convert('RGB')
    img = ImageOps.fit(img, (600, 600), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=82)
    return buffer.getvalue()


def fetch_photo(url):
    """Download a single real photo from a known-good URL. Returns square JPEG bytes or None."""
    try:
        raw = _get(url)
        return to_square_jpeg(raw)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
        return None


def fetch_dummyjson_products(subcategory, limit):
    url = 'https://dummyjson.com/products/category/' + urllib.parse.quote(subcategory) + f'?limit={limit}'
    try:
        return json.loads(_get(url)).get('products', [])
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
        return []


def make_placeholder_image(category_name):
    color = CATEGORY_COLORS.get(category_name, FALLBACK_COLOR)
    img = Image.new('RGB', (600, 600), color=color)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('Arial.ttf', 42)
    except OSError:
        font = ImageFont.load_default()
    text = category_name.upper()
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((600 - w) / 2, (600 - h) / 2), text, fill='white', font=font)
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=70)
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Seeds the catalog with demo products (with real photos where available) across categories.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of demo products to create per category.')
        parser.add_argument('--clear', action='store_true', help='Delete previously seeded demo products first.')
        parser.add_argument('--placeholder-images', action='store_true',
                             help='Skip fetching real photos and use generated color-block placeholders instead.')

    def handle(self, *args, **options):
        count = options['count']
        use_placeholders = options['placeholder_images']

        if options['clear']:
            deleted, _ = Product.objects.filter(description=SEED_MARKER).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} previously seeded rows.'))

        all_category_names = list(DUMMYJSON_PLAN.keys()) + list(CATEGORY_WORDS.keys())
        categories = {c.name: c for c in Category.objects.filter(name__in=all_category_names)}
        if not categories:
            self.stderr.write(self.style.ERROR('No matching categories found - nothing to seed against.'))
            return

        created = 0
        with transaction.atomic():
            for category_name, parts in DUMMYJSON_PLAN.items():
                category = categories.get(category_name)
                if not category:
                    continue
                real_products = []
                for subcategory, limit in parts:
                    real_products.extend(fetch_dummyjson_products(subcategory, limit))
                if not real_products:
                    self.stdout.write(self.style.WARNING(f'  no DummyJSON products fetched for "{category_name}"'))

                for i in range(count):
                    if real_products:
                        source = real_products[i % len(real_products)]
                        cycle = i // len(real_products)
                        title = source['title'] + (f' ({cycle + 1})' if cycle else '')
                        price = source.get('price', 19.99)
                        image_url = (source.get('images') or [None])[0] or source.get('thumbnail')
                    else:
                        title = f'{category_name} Item #{i + 1}'
                        price = 19.99
                        image_url = None

                    product = Product.objects.create(
                        category=category,
                        name=title,
                        description=SEED_MARKER,
                        price=price,
                        warranty_days=random.choice([None, None, 180, 365, 730]),
                        is_active=True,
                    )

                    photo_bytes = None
                    if not use_placeholders and image_url:
                        photo_bytes = fetch_photo(image_url)
                    if photo_bytes is None:
                        photo_bytes = make_placeholder_image(category_name)

                    image = ProductImage(product=product, is_primary=True, alt_text=title)
                    image.image = ContentFile(photo_bytes, name=f'{product.slug}.jpg')
                    image.save()

                    Variant.objects.create(
                        product=product,
                        size=random.choice(['', 'S', 'M', 'L', 'One Size']),
                        color=random.choice(['', 'Black', 'White', 'Blue', 'Red']),
                        sku=f'SEED-{product.pk}',
                        stock=random.choice([0, 5, 10, 25, 50]),
                    )
                    created += 1

                self.stdout.write(f'  ...{category_name}: {count} products')

            for category_name, (adjectives, nouns) in CATEGORY_WORDS.items():
                category = categories.get(category_name)
                if not category:
                    continue

                photo_cache = {}
                if not use_placeholders:
                    for noun in nouns:
                        url = NOUN_PHOTO_URL.get(noun)
                        photo_cache[noun] = fetch_photo(url) if url else None

                for i in range(count):
                    noun = random.choice(nouns)
                    name = f'{random.choice(adjectives)} {noun} #{i + 1}'
                    price = random.choice([9.99, 14.5, 19.99, 24.0, 39.99, 59.5, 89.99, 129.0, 199.99])

                    product = Product.objects.create(
                        category=category,
                        name=name,
                        description=SEED_MARKER,
                        price=price,
                        warranty_days=random.choice([None, None, 180, 365, 730]),
                        is_active=True,
                    )

                    photo_bytes = photo_cache.get(noun) or make_placeholder_image(category_name)

                    image = ProductImage(product=product, is_primary=True, alt_text=name)
                    image.image = ContentFile(photo_bytes, name=f'{product.slug}.jpg')
                    image.save()

                    Variant.objects.create(
                        product=product,
                        size=random.choice(['', 'S', 'M', 'L', 'One Size']),
                        color=random.choice(['', 'Black', 'White', 'Blue', 'Red']),
                        sku=f'SEED-{product.pk}',
                        stock=random.choice([0, 5, 10, 25, 50]),
                    )
                    created += 1

                self.stdout.write(f'  ...{category_name}: {count} products')

        self.stdout.write(self.style.SUCCESS(f'Created {created} demo products across {len(categories)} categories.'))
