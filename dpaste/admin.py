from django.contrib import admin

from dpaste.models import Snippet


class SnippetAdmin(admin.ModelAdmin):
    list_display = (
        '__unicode__',
        'author',
        'lexer',
        'published',
        'expires',
    )


admin.site.register(Snippet, SnippetAdmin)
