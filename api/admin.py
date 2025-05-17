from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AdoptedArea
# from django.contrib.gis.admin import OSMGeoAdmin


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)


@admin.register(AdoptedArea)
class AdoptedAreaAdmin(admin.ModelAdmin):
    list_display = (
        'area_name',
        'user',
        'adoption_type',
        'is_active',
        'city',
        'state',
        'country',
        'created_at',
        'coords',
    )

    list_display_links = ('area_name', 'user')
    list_editable = ('is_active',)

    list_filter = (
        'adoption_type',
        'is_active',
        'state',
        'country',
        'created_at',
    )

    search_fields = (
        'area_name',
        'adoptee_name',
        'email',
        'city',
        'state',
        'country',
    )

    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': (
                'user',
                'area_name',
                'adoptee_name',
                'adoption_type',
                'end_date',
                'is_active',
            )
        }),
        ('Contact', {
            'fields': ('email',),
        }),
        ('Location', {
            'fields': (
                'city',
                'state',
                'country',
                'location',
            ),
            'classes': ('collapse',),
        }),
        ('Extra notes', {
            'fields': ('note',),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    readonly_fields = ('created_at',)

    @admin.display(description='Coordinates')
    def coords(self, obj):
        if obj.location:
            return f"{obj.location.y:.5f}, {obj.location.x:.5f}"  # lat = y, lng = x in GEOS
        return "N/A"


admin.site.register(CustomUser, CustomUserAdmin)
