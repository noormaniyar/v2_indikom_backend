import django_filters
from .models import Product, Category, SubCategory


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    category = django_filters.CharFilter(field_name='category__slug')
    sub_category = django_filters.CharFilter(field_name='sub_category__slug')
    brand = django_filters.CharFilter(field_name='brand', lookup_expr='iexact')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    has_ar = django_filters.BooleanFilter(field_name='has_ar')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    supplier = django_filters.NumberFilter(field_name='supplier__id')

    class Meta:
        model = Product
        fields = ['category', 'sub_category', 'brand', 'has_ar', 'is_featured']

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(discount_price__isnull=False)
        return queryset.filter(discount_price__isnull=True)

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0)
        return queryset.filter(stock=0)
