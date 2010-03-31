from django.shortcuts import render_to_response, get_object_or_404, get_list_or_404
from django.template.context import RequestContext
from django.http import HttpResponseRedirect, HttpResponseBadRequest, HttpResponse, HttpResponseForbidden
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from dpaste.forms import SnippetForm, UserSettingsForm
from dpaste.models import Snippet
from dpaste.highlight import pygmentize, guess_code_lexer
from django.core.urlresolvers import reverse
from django.utils import simplejson
import difflib

def group_and_bridge(request):
    """
    Given the request we can depend on the GroupMiddleware to provide the
    group and bridge.
    """

    # be group aware
    group = getattr(request, 'group', None)
    if group:
        bridge = request.bridge
    else:
        bridge = None

    return group, bridge

def group_context(group, bridge):
    # @@@ use bridge
    ctx = {
        'group': group,
    }
    if group:
        ctx['group_base'] = bridge.group_base_template()
    return ctx

def snippet_new(request, template_name='dpaste/snippet_new.html'):

    group, bridge = group_and_bridge(request)

    if request.method == "POST":
        snippet_form = SnippetForm(data=request.POST, request=request)
        if snippet_form.is_valid():
            request, new_snippet = snippet_form.save(group=group)
            return HttpResponseRedirect(new_snippet.get_absolute_url())
    else:
        snippet_form = SnippetForm(request=request)

    template_context = group_context(group, bridge)
    template_context.update({
        'snippet_form': snippet_form,
    })

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def snippet_details(request, snippet_id, template_name='dpaste/snippet_details.html', is_raw=False):

    group, bridge = group_and_bridge(request)

    # Make queryset suitable for getting the right snippet
    if group:
        snippets = group.content_objects(Snippet)
    else:
        snippets = Snippet.objects.filter(group_object_id=None)
    snippet = get_object_or_404(snippets, secret_id=snippet_id)

    request.session.setdefault('snippet_list', [])

    tree = snippet.get_root()
    tree = tree.get_descendants(include_self=True)

    new_snippet_initial = {
        'content': snippet.content,
        'lexer': snippet.lexer,
    }

    if request.method == "POST":
        snippet_form = SnippetForm(data=request.POST, request=request, initial=new_snippet_initial)
        if snippet_form.is_valid():
            request, new_snippet = snippet_form.save(parent=snippet, group=group)
            return HttpResponseRedirect(new_snippet.get_absolute_url())
    else:
        snippet_form = SnippetForm(initial=new_snippet_initial, request=request)
    
    template_context = group_context(group, bridge)
    template_context.update({
        'snippet_form': snippet_form,
        'snippet': snippet,
        'lines': range(snippet.get_linecount()),
        'tree': tree,
    })

    response = render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

    if is_raw:
        response['Content-Type'] = 'text/plain'
        return response
    else:
        return response

def snippet_delete(request, snippet_id):
    group, bridge = group_and_bridge(request)
    # Make queryset suitable for getting the right snippet
    if group:
        snippets = group.content_objects(Snippet)
    else:
        snippets = Snippet.objects.filter(group_object_id=None)
    snippet = get_object_or_404(snippets, secret_id=snippet_id)
    try:
        snippet_list = request.session['snippet_list']
    except KeyError:
        return HttpResponseForbidden('You have no recent snippet list, cookie error?')
    if not snippet.pk in snippet_list:
        return HttpResponseForbidden('That\'s not your snippet, sucka!')
    snippet.delete()
    return HttpResponseRedirect(reverse('snippet_new'))

def snippet_userlist(request, template_name='dpaste/snippet_list.html'):

    group, bridge = group_and_bridge(request)

    # Make queryset suitable for getting the right snippet
    if group:
        snippets = group.content_objects(Snippet)
    else:
        snippets = Snippet.objects.filter(group_object_id=None)
    
    try:
        snippet_list = get_list_or_404(snippets, pk__in=request.session.get('snippet_list', None))
    except ValueError:
        snippet_list = None
                
    template_context = {
        'snippets_max': getattr(settings, 'MAX_SNIPPETS_PER_USER', 10),
        'snippet_list': snippet_list,
    }

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )


def userprefs(request, template_name='dpaste/userprefs.html'):

    group, bridge = group_and_bridge(request)

    if request.method == 'POST':
        settings_form = UserSettingsForm(request.POST, initial=request.session.get('userprefs', None))
        if settings_form.is_valid():
            request.session['userprefs'] = settings_form.cleaned_data
            settings_saved = True
    else:
        settings_form = UserSettingsForm(initial=request.session.get('userprefs', None))
        settings_saved = False

    template_context = group_context(group, bridge)
    template_context.update({
        'settings_form': settings_form,
        'settings_saved': settings_saved,
    })

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )

def snippet_diff(request, template_name='dpaste/snippet_diff.html'):

    a, b = request.GET.get('a'), request.GET.get('b')

    if (a and b) and (a.isdigit() and b.isdigit()):
        group, bridge = group_and_bridge(request)
        # Make queryset suitable for getting the right snippet
        if group:
            snippets = group.content_objects(Snippet)
        else:
            snippets = Snippet.objects.filter(group_object_id=None)
        try:
            fileA = snippets.get(pk=int(a))
            fileB = snippets.get(pk=int(b))
        except ObjectDoesNotExist:
            return HttpResponseBadRequest(u'Selected file(s) does not exist.')
    else:
        return HttpResponseBadRequest(u'You must select two snippets.')

    if fileA.content != fileB.content:
        d = difflib.unified_diff(
            fileA.content.splitlines(),
            fileB.content.splitlines(),
            'Original',
            'Current',
            lineterm=''
        )
        difftext = '\n'.join(d)
        difftext = pygmentize(difftext, 'diff')
    else:
        difftext = _(u'No changes were made between this two files.')

    template_context = group_context(group, bridge)
    template_context.update({
        'difftext': difftext,
        'fileA': fileA,
        'fileB': fileB,
    })

    return render_to_response(
        template_name,
        template_context,
        RequestContext(request)
    )
    
def guess_lexer(request):
    code_string = request.GET.get('codestring', False)
    response = simplejson.dumps({'lexer': guess_code_lexer(code_string)})
    return HttpResponse(response)
