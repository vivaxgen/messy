
from messy.views import *

from rhombus.views.home import login as rb_login, logout as rb_logout
from rhombus.views import fso
from pyramid.response import FileResponse

import docutils.core
import os

@roles(PUBLIC)
def index(request):

    return render_to_response('messy:templates/generic_page.mako',
        {
            'html': literal('<h2>MESSy: Molecular Epidemiology and Surveillance System</h2>'),
        }, request = request
    )

def login(request):
    return rb_login(request)

def logout(request):
    return rb_logout(request)


@roles(PUBLIC)
def docs(request):

    path = os.path.normpath(request.matchdict.get('path', '') or '/index.rst')
    path = '/' + path if not path.startswith('/') else path
    return fso.serve_file(path, mount_point=('/', "messy:../docs/help"),
                    formatter = lambda abspath: formatter(abspath, request))


def formatter( abspath, request ):

    basepath, ext = os.path.splitext( abspath )

    if ext == '.rst':
        # restructuredtext
        with open(abspath) as f:
            text = f.read()
            content = literal(render_rst(text))

        return render_to_response('messy:templates/generic_page.mako',
            {
                'html': content,
            }, request = request )


    elif ext == '.md':
        raise NotImplementedError

    else:
        return FileResponse( abspath )


def render_rst(text, format='html'):

    parts = docutils.core.publish_parts( text, writer_name=format,
        settings_overrides={'initial_header_level': 2} )
    if format == 'html':
        return parts['html_body']
    return None