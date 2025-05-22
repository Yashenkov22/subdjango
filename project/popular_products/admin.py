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


class PopularProductAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'category',
    )

admin.site.register(PopularProduct, PopularProductAdmin)