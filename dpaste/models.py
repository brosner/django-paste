import datetime
import difflib
import random
import mptt
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import permalink
from django.utils.translation import ugettext_lazy as _
from dpaste.highlight import LEXER_DEFAULT, pygmentize

t = 'abcdefghijkmnopqrstuvwwxyzABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890'
def generate_secret_id(length=4):
    return ''.join([random.choice(t) for i in range(length)]) 

class Snippet(models.Model):
    secret_id = models.CharField(_(u'Secret ID'), max_length=4, blank=True)
    title = models.CharField(_(u'Title'), max_length=120, blank=True)
    author = models.CharField(_(u'Author'), max_length=30, blank=True)
    content = models.TextField(_(u'Content'), )
    content_highlighted = models.TextField(_(u'Highlighted Content'), blank=True)
    lexer = models.CharField(_(u'Lexer'), max_length=30, default=LEXER_DEFAULT)
    published = models.DateTimeField(_(u'Published'), blank=True)
    expires = models.DateTimeField(_(u'Expires'), blank=True, help_text='asdf')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    group_content_type = models.ForeignKey(ContentType, null=True, blank=True)
    group_object_id = models.PositiveIntegerField(null=True, blank=True)
    group = generic.GenericForeignKey('group_content_type', 'group_object_id')
    

    class Meta:
        ordering = ('-published',)
        unique_together = [('group_content_type', 'group_object_id', 'secret_id')]

    def get_linecount(self):
        return len(self.content.splitlines())

    def content_splitted(self):
        return self.content_highlighted.splitlines()

    def save(self):
        if not self.pk:
            self.published = datetime.datetime.now()
            self.secret_id = generate_secret_id()
        self.content_highlighted = pygmentize(self.content, self.lexer)
        super(Snippet, self).save()

    def get_absolute_url(self):
        kwargs = {'snippet_id': self.secret_id}
        if self.group:
            bridge = self.group.content_bridge
            url = bridge.reverse('snippet_details', self.group, kwargs=kwargs)
        else:
            url = reverse('snippet_details', kwargs=kwargs)
        return url

    def __unicode__(self):
        return '%s' % self.secret_id

mptt.register(Snippet, order_insertion_by=['content'])
