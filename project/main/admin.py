from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.db.models import Count, Sum, Value, OuterRef, Subquery, F
from django.db.models.functions import Coalesce

from datetime import datetime, timedelta

from .models import Users, WbProducts, OzonProducts, UTM, UserProducts, Products

from rangefilter.filters import (
    DateRangeFilterBuilder,
    DateTimeRangeFilterBuilder,
    NumericRangeFilterBuilder,
    DateRangeQuickSelectListFilterBuilder,
)


admin.site.unregister(User)
admin.site.unregister(Group)


class CustomDateTimeFilter(admin.SimpleListFilter):
    title = 'Фильтры по дате'
    parameter_name = 'custom_date_filter'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Сегодня'),
            ('yesterday', 'Вчера'),
            ('this_week', 'В течении 7 дней'),
            ('this_month', 'В этом месяце'),
            ('this_year', 'В этом году'),
            ('date_exists', 'Дата указана'),
            ('date_not_exists', 'Дата не указана'),
        )

    def queryset(self, request, queryset):
        today = datetime.now()
        # print(today)
        if self.value() == 'today':
            start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            return queryset.filter(time_create__range=(start_of_today, end_of_today))
        elif self.value() == 'yesterday':
            start_of_yesterday = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_of_yesterday = today.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
            return queryset.filter(time_create__range=(start_of_yesterday, end_of_yesterday))
        elif self.value() == 'this_week':
            # start_of_week = today - timedelta(days=today.weekday())
            start_of_week = today - timedelta(days=6, hours=23, minutes=59, seconds=59)

            # end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
            end_of_week = today

            return queryset.filter(time_create__range=(start_of_week, end_of_week))
        elif self.value() == 'this_month':
            start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            return queryset.filter(time_create__range=(start_of_month, end_of_month))
        elif self.value() == 'this_year':
            start_of_year = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_of_year = today.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            return queryset.filter(time_create__range=(start_of_year, end_of_year))
        elif self.value() == 'date_exists':
            return queryset.exclude(time_create__isnull=True)
        elif self.value() == 'date_not_exists':
            return queryset.filter(time_create__isnull=True)
        
        return queryset
    

class UTMSourceFilter(admin.filters.SimpleListFilter):
    title = 'Кастомный UTM фильтр'
    parameter_name = 'utm_source_start'

    def lookups(self, request, model_admin):
        request_session = request.session

        # Получаем уникальные значения начала строки
        # utm_source_start = request.GET.get('utm_source_start')
        print('lookup',request.GET)
        print('request session', request_session.__dict__)
        # if not utm_source_start:

        if request_session.get('prefix_utm') and \
            request_session.get('second_part_utm'):
            print('22')

        utm_source = self.value()
        print(utm_source)
        if not utm_source:
            prefixes = Users.objects.filter(utm_source__isnull=False)\
                                    .values_list('utm_source', flat=True)\
                                    .distinct()

            unique_prefix =  [('_'.join(prefix.split('_')[:2]), '_'.join(prefix.split('_')[:2])) \
                                for prefix in set(prefixes) if prefix is not None]
            
            request_session['prefix_utm'] = None
            request_session['second_part_utm'] = None

            return sorted(set(unique_prefix))


            # return [('_'.join(prefix.split('_')[:2]), '_'.join(prefix.split('_')[:2])) \
            #         for prefix in set(prefixes) if prefix is not None]
        else:
            if utm_source[:2].isdigit():
                prefix_utm = request_session.get('prefix_utm')
                prefixes = Users.objects.filter(utm_source__isnull=False,
                                                utm_source__endswith=utm_source,
                                                utm_source__startswith=prefix_utm)\
                                        .values_list('utm_source', flat=True)\
                                        .distinct()
                
                request.session['second_part_utm'] = utm_source

            check_value = (utm_source[:2].isdigit()) or (utm_source == '--')
            
            if not check_value:
                prefixes = Users.objects.filter(utm_source__isnull=False,
                                                utm_source__startswith=utm_source)\
                                        .values_list('utm_source', flat=True)\
                                        .distinct()
                
                unique_prefix = [('_'.join(prefix.split('_')[2:]), '_'.join(prefix.split('_')[2:])) \
                                 for prefix in set(prefixes) if prefix is not None]
                
                request.session['prefix_utm'] = utm_source
                
                return sorted(set(unique_prefix))

                # return [('_'.join(prefix.split('_')[2:]), '_'.join(prefix.split('_')[2:])) \
                #         for prefix in set(prefixes) if prefix is not None]
            else:
                # request.session['prefix_utm'] = None
                return [('--', '--')]
        # return [(prefix, prefix) for prefix in set(prefixes) if prefix is not None]


    def queryset(self, request, queryset):
        request_session = request.session
        
        # if any(key for key in request.GET if key.startswith('time_create')):
        #     request.GET['time_create__isnull'] = ['False']
        # else:
        #     try:
        #         del request.GET['time_create__isnull']
        #     except Exception as ex:
        #         print(ex)
        print(request.GET)
        print('request session', request_session.__dict__)
        # utm_source_start = request.GET.get('utm_source_start')
        utm_source = self.value()
        # print(utm_source)
        # print(22)
        if utm_source:
        #     # if not utm_source_start:
            check_value = utm_source[:2].isdigit()
            
            if not check_value:
                queryset = queryset.filter(utm_source__startswith=utm_source,
                                           utm_source__isnull=False)
            else:
                prefix_utm = request_session.get('prefix_utm')
                if prefix_utm:
                    queryset = queryset.filter(utm_source__startswith=prefix_utm,
                                            utm_source__endswith=utm_source,
                                            utm_source__isnull=False)
                    
                    # request.session['prefix_utm'] = None

                # utm_source_start = utm_source_start[0]
                # queryset = queryset.filter(utm_source__startswith=utm_source_start)
        # print(queryset)
        return queryset


class UTMInline(admin.StackedInline):
    model = UTM
    extra = 0
    classes = [
        'collapse',
        ]

    def has_change_permission(self, request, obj = ...):
        return False

#Отображение комментариев в админ панели
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        # 'tg_id',
        # 'link_count',
        # 'is_active',
        'get_utm_source',
        'utm__utm_campaign',
        'product_count',
        'time_create',
    )
    inlines = [UTMInline]

    def get_utm_source(self, obj):
        return obj.utm_source if obj.utm_source and obj.utm_source.startswith('direct') else obj.utm.source
    
    get_utm_source.short_description = 'UTM источник'

    readonly_fields = (
        # 'link_count',
        'username',
        'first_name',
        'last_name',
        'utm_source',
        'time_create',
        # 'subscription',
        'product_count',
    )

    ordering = (
        '-time_create',
    )

    list_filter = (
        CustomDateTimeFilter,
        ("time_create", DateRangeFilterBuilder()),
        # UTMSourceFilter,
        # ('time_create', DateRangeQuickSelectListFilterBuilder()),
        # ("time_create", NumericRangeFilterBuilder()),
        # 'time_create',
        # UTMSourceSecondPartFilter,
        )
    
    fieldsets = [
        (
            None,
            {
                "fields": ['username',
                           "first_name",
                           "last_name",
                           "subscription",
                           "utm_source",
                           "product_count",
                        #    'related_utm',
                           "time_create"]
            },
        ),
    ]

    def product_count(self, obj):
        wb_products = obj.wb_product_count if obj.wb_product_count else 0
        ozon_products = obj.ozon_product_count if obj.ozon_product_count else 0

        product_count = wb_products + ozon_products

        return f'{product_count} | wb: {wb_products} | ozon: {ozon_products}'
    

    product_count.short_description = 'Число продуктов'
    product_count.admin_order_field = 'all_product_count'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        # wb_products_subquery = WbProducts.objects.filter(
        #     user_id=OuterRef('tg_id')
        # ).values('user_id').annotate(
        #     total_count=Coalesce(Count('id'), Value(0))
        # ).values('total_count')

        wb_products_subquery = UserProducts.objects.select_related('product').filter(
            user_id=OuterRef('tg_id'),
            product__product_marker='wb',
        ).values('user_id').annotate(
            total_count=Coalesce(Count('id'), Value(0))
        ).values('total_count')

        # ozon_products_subquery = OzonProducts.objects.filter(
        #     user_id=OuterRef('tg_id')
        # ).values('user_id').annotate(
        #     total_count=Coalesce(Count('id'), Value(0))
        # ).values('total_count')

        ozon_products_subquery = UserProducts.objects.select_related('product').filter(
            user_id=OuterRef('tg_id'),
            product__product_marker='ozon',
        ).values('user_id').annotate(
            total_count=Coalesce(Count('id'), Value(0))
        ).values('total_count')

        return queryset.select_related('utm').annotate(wb_product_count=Subquery(wb_products_subquery),
                                                       ozon_product_count=Subquery(ozon_products_subquery),
                                                       all_product_count=Coalesce(F('wb_product_count'), Value(0)) + Coalesce(F('ozon_product_count'), Value(0)))
    

@admin.register(UTM)
class UTMAdmin(admin.ModelAdmin):
    list_display = (
        'pretty_user',
        'source',
    )

    def pretty_user(seld, obj):
        return f'{obj.user.tg_id} {obj.user.username}'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')