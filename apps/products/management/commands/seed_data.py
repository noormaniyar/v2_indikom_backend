"""
Management command to seed the database with initial categories,
sub-categories, attribute definitions, and subscription plans.

Usage:
    python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed initial categories, attributes, and subscription plans'

    def handle(self, *args, **options):
        self.seed_categories()
        self.seed_attributes()
        self.seed_subscription_plans()
        self.stdout.write(self.style.SUCCESS('✅ Seed data loaded successfully.'))

    # ─── CATEGORIES ───────────────────────────────────────────────────────────
    def seed_categories(self):
        from apps.products.models import Category, SubCategory

        CATEGORY_TREE = {
            'Appliances': {
                'icon': None,
                'children': {
                    'Kitchen': ['Toaster', 'Air Fryer', 'Mixer Grinder', 'Microwave', 'Coffee Maker', 'Juicer'],
                    'Cooling': ['Air Conditioner', 'Refrigerator', 'Air Cooler', 'Table Fan', 'Ceiling Fan'],
                    'Cleaning': ['Vacuum Cleaner', 'Washing Machine', 'Dishwasher', 'Wet & Dry Cleaner'],
                    'Personal Care': ['Hair Dryer', 'Electric Shaver', 'Trimmer', 'Straightener'],
                },
            },
            'Electronics': {
                'children': {
                    'Television': ['LED TV', 'OLED TV', 'Smart TV', 'Projector'],
                    'Audio': ['Speakers', 'Headphones', 'Earphones', 'Soundbar'],
                    'Computers': ['Laptop', 'Desktop', 'Monitor', 'Keyboard', 'Mouse'],
                    'Mobile & Tablets': ['Smartphones', 'Tablets', 'Smartwatch', 'Phone Accessories'],
                    'Cameras': ['DSLR', 'Mirrorless', 'Action Camera', 'Webcam'],
                },
            },
            'Furniture': {
                'children': {
                    'Living Room': ['Sofa', 'Coffee Table', 'TV Unit', 'Bookshelf', 'Recliners'],
                    'Bedroom': ['Bed', 'Wardrobe', 'Dresser', 'Nightstand', 'Study Table'],
                    'Dining': ['Dining Table', 'Dining Chair', 'Bar Stool', 'Sideboard'],
                    'Office': ['Office Chair', 'Computer Desk', 'Filing Cabinet', 'Bookcase'],
                    'Outdoor': ['Garden Chair', 'Patio Table', 'Swing', 'Hammock'],
                },
            },
            'Doors & Windows': {
                'children': {
                    'Doors': ['Panel Door', 'Pivot Door', 'Sliding Door', 'Glass Door', 'Security Door'],
                    'Windows': ['Casement Window', 'Sliding Window', 'Bay Window', 'Skylight'],
                    'Hardware': ['Door Handles', 'Hinges', 'Door Locks', 'Closers'],
                },
            },
            'Decor': {
                'children': {
                    'Wall Decor': ['Wall Art', 'Mirrors', 'Clocks', 'Wallpaper', 'Photo Frames'],
                    'Lighting': ['Ceiling Lights', 'Floor Lamps', 'Table Lamps', 'String Lights', 'LED Strips'],
                    'Rugs & Carpets': ['Area Rugs', 'Runner Rugs', 'Bath Mats', 'Door Mats'],
                    'Cushions & Throws': ['Cushion Covers', 'Throw Blankets', 'Pillow Sets'],
                },
            },
            'Stationery': {
                'children': {
                    'Writing': ['Pens', 'Pencils', 'Markers', 'Highlighters', 'Ink'],
                    'Paper Products': ['Notebooks', 'Notepads', 'Sticky Notes', 'Printer Paper'],
                    'Office Supplies': ['Staplers', 'Scissors', 'Tape', 'Clips', 'Folders'],
                    'Art Supplies': ['Sketch Books', 'Watercolors', 'Canvases', 'Brushes'],
                },
            },
            'Clothing': {
                'children': {
                    'Men': ["Men's T-Shirts", "Men's Shirts", "Men's Trousers", "Men's Jackets", "Men's Ethnic"],
                    'Women': ["Women's Tops", "Women's Dresses", "Women's Sarees", "Women's Kurtas", "Women's Jeans"],
                    'Kids': ["Boys Clothing", "Girls Clothing", "Baby Clothing", "School Uniform"],
                    'Footwear': ['Sneakers', 'Formal Shoes', 'Sandals', 'Boots', 'Slippers'],
                    'Accessories': ['Bags', 'Belts', 'Scarves', 'Sunglasses', 'Wallets'],
                },
            },
            'Sports & Fitness': {
                'children': {
                    'Exercise Equipment': ['Treadmill', 'Dumbbells', 'Resistance Bands', 'Yoga Mat'],
                    'Sports': ['Cricket', 'Football', 'Badminton', 'Tennis', 'Swimming'],
                    'Outdoor Recreation': ['Camping Gear', 'Cycling', 'Hiking', 'Trekking'],
                },
            },
        }

        created_cats = 0
        created_subcats = 0

        for main_name, main_data in CATEGORY_TREE.items():
            main_slug = slugify(main_name)
            main_cat, created = Category.objects.get_or_create(
                slug=main_slug,
                defaults={
                    'name': main_name,
                    'is_active': True,
                    'sort_order': list(CATEGORY_TREE.keys()).index(main_name),
                    'parent': None,
                }
            )
            if created:
                created_cats += 1

            for sub_name, product_types in main_data.get('children', {}).items():
                sub_slug = slugify(f"{main_name}-{sub_name}")
                sub_cat, sub_created = Category.objects.get_or_create(
                    slug=sub_slug,
                    defaults={
                        'name': sub_name,
                        'is_active': True,
                        'parent': main_cat,
                    }
                )
                if sub_created:
                    created_cats += 1

                # Also create SubCategory for backward compatibility
                old_sub, old_created = SubCategory.objects.get_or_create(
                    slug=sub_slug,
                    defaults={
                        'name': sub_name,
                        'category': main_cat,
                        'is_active': True,
                    }
                )
                if old_created:
                    created_subcats += 1

                for pt_name in product_types:
                    pt_slug = slugify(f"{main_name}-{sub_name}-{pt_name}")
                    pt, pt_created = Category.objects.get_or_create(
                        slug=pt_slug,
                        defaults={
                            'name': pt_name,
                            'is_active': True,
                            'parent': sub_cat,
                        }
                    )
                    if pt_created:
                        created_cats += 1

        self.stdout.write(f'  📁 Categories: {created_cats} created, {created_subcats} legacy subcats')

    # ─── ATTRIBUTES ───────────────────────────────────────────────────────────
    def seed_attributes(self):
        from apps.products.models import AttributeDefinition, AttributeValue

        GLOBAL_ATTRIBUTES = {
            'Color': ['Black', 'White', 'Grey', 'Brown', 'Beige', 'Navy Blue', 'Green', 'Red', 'Yellow', 'Pink', 'Orange', 'Purple', 'Gold', 'Silver'],
            'Size': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL'],
        }

        CATEGORY_ATTRIBUTES = {
            'Sofa': {
                'Seating Capacity': ['1-Seater', '2-Seater', '3-Seater', '4-Seater', 'L-Shape', 'U-Shape'],
                'Material': ['Fabric', 'Leather', 'Velvet', 'Linen', 'Wool', 'Faux Leather', 'Microfiber'],
                'Frame Material': ['Solid Wood', 'Metal', 'Engineered Wood', 'Teak', 'Oak', 'Sheesham'],
            },
            'Television': {
                'Screen Size': ['24 inch', '32 inch', '40 inch', '43 inch', '50 inch', '55 inch', '65 inch', '75 inch', '85 inch'],
                'Display Type': ['LED', 'OLED', 'QLED', 'AMOLED', 'IPS'],
                'Resolution': ['HD Ready', 'Full HD', '4K Ultra HD', '8K'],
            },
            'Toaster': {
                'Slice Capacity': ['2 Slice', '4 Slice', '6 Slice'],
                'Wattage': ['700W', '800W', '1000W', '1200W', '1500W'],
            },
            'Refrigerator': {
                'Type': ['Single Door', 'Double Door', 'Side by Side', 'French Door', 'Mini'],
                'Capacity': ['150L', '190L', '250L', '300L', '350L', '400L', '500L', '600L+'],
                'Star Rating': ['1 Star', '2 Star', '3 Star', '4 Star', '5 Star'],
            },
            'Door': {
                'Style': ['Panel', 'Pivot', 'Sliding', 'Flush', 'Dutch', 'Barn'],
                'Material': ['Wood', 'Glass', 'Steel', 'Composite', 'PVC', 'Aluminium'],
                'Finish': ['Natural', 'Painted', 'Laminated', 'Veneer', 'PU Coated'],
            },
        }

        created = 0

        # Global attributes
        for attr_name, values in GLOBAL_ATTRIBUTES.items():
            attr, _ = AttributeDefinition.objects.get_or_create(
                name=attr_name, category=None,
                defaults={'is_global': True}
            )
            for i, val in enumerate(values):
                _, val_created = AttributeValue.objects.get_or_create(
                    attribute=attr, value=val,
                    defaults={'sort_order': i}
                )
                if val_created:
                    created += 1

        # Category-specific attributes
        from apps.products.models import Category
        for category_name, attrs in CATEGORY_ATTRIBUTES.items():
            # Find matching category (case-insensitive)
            cat = Category.objects.filter(name__icontains=category_name).first()
            for attr_name, values in attrs.items():
                attr, _ = AttributeDefinition.objects.get_or_create(
                    name=attr_name, category=cat,
                    defaults={'is_global': False}
                )
                for i, val in enumerate(values):
                    _, val_created = AttributeValue.objects.get_or_create(
                        attribute=attr, value=val,
                        defaults={'sort_order': i}
                    )
                    if val_created:
                        created += 1

        self.stdout.write(f'  🎨 Attribute values: {created} created')

    # ─── SUBSCRIPTION PLANS ───────────────────────────────────────────────────
    def seed_subscription_plans(self):
        from apps.subscriptions.models import SubscriptionPlan

        PLANS = [
            {
                'name': 'Supplier Basic',
                'plan_type': SubscriptionPlan.PlanType.SUPPLIER_BASIC,
                'description': 'Perfect for small sellers getting started.',
                'price_monthly': 499,
                'price_yearly': 4999,
                'max_products': 50,
                'commission_discount': 0,
                'features': [
                    'Up to 50 products',
                    'Basic analytics',
                    'Standard support',
                    'Product image uploads',
                ],
            },
            {
                'name': 'Supplier Pro',
                'plan_type': SubscriptionPlan.PlanType.SUPPLIER_PRO,
                'description': 'For growing businesses with more product needs.',
                'price_monthly': 1499,
                'price_yearly': 14999,
                'max_products': 500,
                'commission_discount': 2,
                'features': [
                    'Up to 500 products',
                    'Advanced analytics',
                    'Priority support',
                    'AR product preview',
                    'Bulk product upload',
                    '2% commission reduction',
                ],
            },
            {
                'name': 'Supplier Enterprise',
                'plan_type': SubscriptionPlan.PlanType.SUPPLIER_ENTERPRISE,
                'description': 'Unlimited scale for large enterprises.',
                'price_monthly': 4999,
                'price_yearly': 49999,
                'max_products': 0,  # unlimited
                'commission_discount': 5,
                'features': [
                    'Unlimited products',
                    'Full analytics dashboard',
                    'Dedicated account manager',
                    'AR & 3D preview',
                    'API access',
                    'Custom branding',
                    '5% commission reduction',
                ],
            },
        ]

        created = 0
        for plan_data in PLANS:
            _, plan_created = SubscriptionPlan.objects.get_or_create(
                plan_type=plan_data['plan_type'],
                defaults=plan_data
            )
            if plan_created:
                created += 1

        self.stdout.write(f'  💳 Subscription plans: {created} created')
