from django.contrib import admin

from .models import CategoryChannelLink, Category, ChannelLink, PopularProduct

# Register your models here.

class CategoryChannelLinkInline(admin.TabularInline):
    model = CategoryChannelLink
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    inlines = [
        CategoryChannelLinkInline,
    ]

admin.site.register(Category, CategoryAdmin)


class ChannelLinkAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )

admin.site.register(ChannelLink, ChannelLinkAdmin)



class CustomCategoryFilter(admin.SimpleListFilter):
    title = 'Direction'
    parameter_name = 'direction'

    def lookups(self, request, model_admin):
        # Используйте select_related для оптимизации запроса
        directions = Category.objects.select_related('parent').distinct()
        return [(d.id, str(d)) for d in directions]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__id=self.value())
        return queryset


class PopularProductAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'category',
    )

    raw_id_fields = (
        'category',
        'product',
    )

    list_filter = (
        CustomCategoryFilter,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product',
                                                            'category',
                                                            'category__parent')

admin.site.register(PopularProduct, PopularProductAdmin)